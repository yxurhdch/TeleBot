-- Database Schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL
);

CREATE TABLE user_words (
    word_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    en_word VARCHAR(255) NOT NULL,
    ru_word VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_word UNIQUE (user_id, en_word)
);

CREATE INDEX user_words_user_id_idx ON user_words(user_id);