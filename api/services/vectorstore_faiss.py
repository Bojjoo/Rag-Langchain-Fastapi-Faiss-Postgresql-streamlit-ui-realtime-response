from api.services import *


class VectorStore:
    def __init__(self, user_id=None):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
                                                            length_function=len)
        self.model_embedding = model_embedding
        try:
            self.user_db = FAISS.load_local(f'{USER_DATABASE}/{user_id}', self.model_embedding,
                                            allow_dangerous_deserialization=True)
            self.user_retriever = self.user_db.as_retriever(search_kwargs=SEARCH_KWARGS, search_type=SEARCH_TYPE)
            documents = list(self.user_db.docstore._dict.values())
            self.user_bm25_retriever = BM25Retriever.from_documents(documents)
            self.user_bm25_retriever.k = 25
        except:
            self.user_db = None
            self.user_retriever = None
            self.user_bm25_retriever = None

    # For user
    def split_document(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.txt':
            loader = TextLoader(file_path)
        elif file_extension == '.csv':
            loader = CSVLoader(file_path)
        elif file_extension == '.docx':
            loader = UnstructuredWordDocumentLoader(file_path)
        else:
            raise ValueError("Unsupported file type")
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        return chunks

    # Lưu vào vectorstore
    def create_vectorstore(self, chunks):
        db = FAISS.from_documents(chunks, self.model_embedding)
        # db.save_local(USER_DATABASE)
        return db

    # thêm vào vectorstore
    def merge_to_vectorstore(self, old_db, new_db, user_id):
        old_db.merge_from(new_db)
        old_db.save_local(f'{USER_DATABASE}/{user_id}')
        return old_db

    # xóa khỏi vectorstore theo id của chunks
    def delete_from_vectorstore(self, file_name, user_id):
        # db_user, retriever_user = self.check_user_db(user_id)
        db_user = self.user_db
        docstore = db_user.docstore._dict
        key_delete = []
        for key, values in docstore.items():
            if values.metadata['source'].endswith(f"{file_name}"):
                key_delete.append(key)
        db_user.delete(key_delete)
        db_user.save_local(f"{USER_DATABASE}/{user_id}")
        os.remove(f"{USER_DOCUMENT}/{user_id}/{file_name}")
        sql_conn.delete_file(file_name, user_id)

    # upload file và lưu vào vectorstore faiss, lưu file vào folder của conversation_id
    def upload_file(self, file: UploadFile = File(...), user_id: str = Form(...)):
        name = file.filename
        if name.endswith('.pdf') or name.endswith('docx'):
            # Lấy ra file size
            file.file.seek(0, os.SEEK_END)
            file_size = round(file.file.tell() / (1024 * 1024), 2)
            file.file.seek(0)
            result = sql_conn.save_file_detail(file.filename, file_size, user_id)

            # Nếu result =1: thỏa mãn yêu cầu về total_size <50 và file_size <20
            if result == 1:
                # Lưu file vào folder
                folder_path = f"{USER_DOCUMENT}/{user_id}"
                os.makedirs(folder_path, exist_ok=True)

                with open(f"{folder_path}/{file.filename}", "wb") as buff:
                    shutil.copyfileobj(file.file, buff)
                chunks = self.split_document(f"{folder_path}/{file.filename}")

                # bỏ vào vectorstore mới
                new_db_for_user = self.create_vectorstore(chunks)
                try:
                    # Nếu đã có db, hợp nhất db cũ với db mới
                    db_user = self.user_db
                    merged_db_user = self.merge_to_vectorstore(db_user, new_db_for_user, user_id)
                    # return merged_db_user
                except:  # Nếu chưa có db
                    new_db_for_user.save_local(f'{USER_DATABASE}/{user_id}')
                    # return new_db_for_user

                return f"Successfully uploaded {file.filename}, num_splits: {len(chunks)}"
            else:
                return """Failed to upload document, the total size limit is 50Mb and the file size limit is 20Mb.
                        You can delete existed document to upload an other one!"""
        else:
            return "Only pdf, docx files are supported"

    # For system
    def create_db_from_files(self):
        loaders = [
            DirectoryLoader(SYSTEM_DOCUMENT, glob="*.pdf", loader_cls=PyPDFLoader),
            DirectoryLoader(SYSTEM_DOCUMENT, glob="*.txt", loader_cls=TextLoader),
            DirectoryLoader(SYSTEM_DOCUMENT, glob="*.docx", loader_cls=UnstructuredWordDocumentLoader),
        ]
        documents = []
        for loader in loaders:
            documents.extend(loader.load())
        chunks = self.text_splitter.split_documents(documents)

        # Embedding
        db = FAISS.from_documents(chunks, self.model_embedding)
        db.save_local(SYSTEM_DATABASE)
        return db
