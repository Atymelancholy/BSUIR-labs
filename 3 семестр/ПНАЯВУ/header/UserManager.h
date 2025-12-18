//
// Created by atyme on 30.10.2024.
//

#ifndef LAB_2_USERMANAGER_H
#define LAB_2_USERMANAGER_H

#include "../header/UserManager.h"
#include <unordered_map>
#include <iostream>
#include <fstream>
#include <sstream>

struct User {
    std::string username;
    std::string password;
};

class UserManager {
private:
    std::unordered_map<std::string, User> users;

    void loadUsers() {
        std::ifstream file("users.txt");
        std::string username, password;
        while (file >> username >> password) {
            users[username] = {username, password};
        }
        file.close();
    }

    void saveUser(const User& user) {
        std::ofstream file("users.txt", std::ios::app);
        file << user.username << " " << user.password << "\n";
        file.close();
    }

public:
    UserManager() {
        loadUsers();
    }

    bool registerUser(const std::string& username, const std::string& password) {
        if (users.find(username) != users.end()) {
            std::cout << "Пользователь с таким именем уже существует.\n";
            return false;
        }
        users[username] = {username, password};
        saveUser({username, password});
        std::cout << "Регистрация успешна!\n";
        return true;
    }

    bool loginUser(const std::string& username, const std::string& password) {
        if (users.find(username) != users.end() && users[username].password == password) {
            std::cout << "Добро пожаловать, " << username << "!\n";
            return true;
        }
        std::cout << "Неверное имя пользователя или пароль.\n";
        return false;
    }

    void saveTestResult(const std::string& username, int situationalScore, int personalScore) {
        std::ofstream file(username + "_results.txt", std::ios::app);
        file << situationalScore << " " << personalScore << "\n";
        file.close();
    }

    void viewTestHistory(const std::string& username) {
        std::ifstream file(username + "_results.txt");
        if (!file.is_open()) {
            std::cout << "История тестов не найдена.\n";
            return;
        }

        std::string line;
        std::cout << "История тестов для пользователя " << username << ":\n";
        while (std::getline(file, line)) {
            std::cout << line << std::endl;
        }
        file.close();
    }

    void compareResults(const std::string& username, int situationalScore, int personalScore) {
        std::ifstream file(username + "_results.txt");
        if (!file.is_open()) {
            std::cout << "История тестов не найдена.\n";
            return;
        }

        std::string line;
        int previousSituationalScore = 0;
        int previousPersonalScore = 0;
        int count = 0;

        while (std::getline(file, line)) {
            std::istringstream iss(line);
            int situational, personal;
            iss >> situational >> personal;

            previousSituationalScore += situational;
            previousPersonalScore += personal;
            count++;
        }

        if (count > 0) {
            previousSituationalScore /= count;
            previousPersonalScore /= count;

            std::cout << "\nСравнение с предыдущими результатами:\n";
            std::cout << "Ситуативная тревожность: " << situationalScore << " (предыдущее: " << previousSituationalScore << ")\n";
            std::cout << "Личностная тревожность: " << personalScore << " (предыдущее: " << previousPersonalScore << ")\n";

            if (situationalScore > previousSituationalScore) {
                std::cout << "Ваши результаты ухудшились. Рекомендуем обратиться к специалисту.\n";
            } else if (situationalScore < previousSituationalScore) {
                std::cout << "Молодец! Ваши результаты улучшились.\n";
            } else {
                std::cout << "Результаты остались без изменений. Пожелаем вам улучшений.\n";
            }
        }

        file.close();
    }
};



#endif //LAB_2_USERMANAGER_H
