package com.example.bookblog;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

@SpringBootApplication
@EnableAspectJAutoProxy
public class BookBlogApplication {

	public static void main(String[] args) {
		SpringApplication.run(BookBlogApplication.class, args);
	}

}
