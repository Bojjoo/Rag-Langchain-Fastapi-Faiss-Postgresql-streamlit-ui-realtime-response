CREATE TABLE users (
user_id varchar(20) PRIMARY KEY,
username VARCHAR(50) NOT NULL unique,
password varchar(50) not null,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
    conversation_id VARCHAR(20) primary key,
	conversation_name varchar(20) not null,
    user_id VARCHAR(20) REFERENCES users(user_id),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE
);

CREATE TABLE messages (
message_id int,
conversation_id varchar(20) references conversations(conversation_id),
sender VARCHAR(50) NOT NULL,
message_text TEXT not null,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
Primary key(message_id,conversation_id)
);

CREATE TABLE files(
file_id varchar(20) primary key,
file_name varchar(50) not null,
size real not null,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
user_id VARCHAR(20) REFERENCES users(user_id)
);

CREATE TABLE prompts(
prompt_id varchar(20) primary key,
title varchar(200) not null,
prompt_text varchar(10000) not null,
user_id VARCHAR(20) REFERENCES users(user_id),
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE apikeys(
user_id varchar(20) references users(user_id),
type varchar(20) CHECK (type IN ('openaikey', 'geminikey')),
key varchar(150) default null,
primary key(user_id, type)
);


-- Tạo function để tự động tính `message_id` cho mỗi `conversation_id`.
CREATE OR REPLACE FUNCTION calculate_message_id_new()
RETURNS TRIGGER AS $$
DECLARE
    max_id INT;
BEGIN
    -- Lấy `message_id` lớn nhất trong mỗi `conversation_id`
    SELECT COALESCE(MAX(message_id), 0) + 1 INTO max_id
    FROM messages
    WHERE conversation_id = NEW.conversation_id;

    -- Gán `message_id` mới cho bản ghi
    NEW.message_id := max_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Tạo trigger để tự động cập nhật `message_id` cho từng bản ghi mới
CREATE TRIGGER set_message_id_new
BEFORE INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION calculate_message_id_new();
