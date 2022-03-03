drop database if exists photo_sharing_website;
create database if not exists photo_sharing_website;
use photo_sharing_website;

create table if not exists users(
	user_id varchar(255) not null primary key,
    first_name varchar(255) not null,
    last_name varchar(255) not null,
    email varchar(255) not null,
    date_of_birth date not null,
    hometown varchar(255) not null,
    gender varchar(255) not null,
    user_password varchar(255) not null,
    score int not null);
    
create table if not exists friends(
	user1 varchar(255) not null,
    user2 varchar(255) not null,
    accepted boolean not null);
    
create table if not exists albums(
	album_id int not null primary key auto_increment,
    owner_id varchar(255) not null,
    album_name varchar(255) not null,
    date_of_creation date not null);
    
create table if not exists photos(
    photo_id int not null auto_increment primary key,
    album_id int not null,
    caption varchar(255),
    photo longtext not null,
    score int not null);
    
create table if not exists tags(
	photo_described int not null,
    word varchar(255));
    
create table if not exists comments(
	comment_id int not null auto_increment primary key,
    comment_text varchar(255) not null,
    owner_id varchar(255) not null,
    date_posted date not null);

    
alter table friends add foreign key (user1) references users(user_id);
alter table friends add foreign key (user2) references users(user_id);
alter table albums add foreign key (owner_id) references users(user_id);
alter table photos add foreign key (album_id) references albums(album_id);
alter table tags add foreign key (photo_described) references photos(photo_id);
alter table comments add foreign key (owner_id) references users(user_id);



insert into users(user_id, first_name, last_name, email, date_of_birth, hometown, gender, user_password, score) values ("khalid750hh", "Khalid", "Almaimouni", "khalid75@bu.edu", "2000-4-03" , "Riyadh, Saudi Arabia", "Male", "PASSWORD", 0);
insert into users(user_id, first_name, last_name, email, date_of_birth, hometown, gender, user_password, score) values ("test123", "test", "test", "test@test.com", "2000-4-03" , "test", "test", "test123", 0);


select * from users;