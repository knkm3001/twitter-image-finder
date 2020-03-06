create database IF NOT EXISTS twitter;

create table  IF NOT EXISTS twitter.timeline (
                tweet_ID bigint(18) NOT NULL PRIMARY KEY,
                insert_date datetime,
                user_name varchar(50),
                user_screen_name varchar(15),
                user_ID bigint(18),
                RT_flg bit(1) NOT NULL DEFAULT b'0',
                RTed_user_name varchar(50) DEFAULT NULL,
                RTed_user_screen_name varchar(15) DEFAULT NULL,
                RTed_user_ID bigint(18) DEFAULT NULL,
                created_at datetime,
                text varchar(512),
                picture_flg bit(1) NOT NULL DEFAULT b'0',
                media_url varchar(512) DEFAULT NULL,
                media_path varchar(512) DEFAULT NULL
            )default character set utf8mb4;