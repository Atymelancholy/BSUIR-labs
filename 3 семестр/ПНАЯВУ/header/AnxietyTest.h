//
// Created by atyme on 30.10.2024.
//

#ifndef LAB_2_ANXIETYTEST_H
#define LAB_2_ANXIETYTEST_H

#include <iostream>
#include <vector>
#include <limits>


class AnxietyTest {
protected:
    std::vector<int> answers;
    std::vector<std::string> questions;
    int numQuestions;

public:
    AnxietyTest(int numQuestions, const std::vector<std::string>& questions)
            : numQuestions(numQuestions), questions(questions) {
        answers.resize(numQuestions);
    }

    void takeTest() {
        std::cout << "Ответьте на следующие вопросы, выбрав цифру от 1 до 4\n(1 - нет, это не совсем так; 2 - пожалуй, так; 3 - верно; 4 - совершенно верно):\n";
        for (int i = 0; i < numQuestions; ++i) {
            std::cout << "Вопрос " << (i + 1) << ": " << questions[i] << std::endl;
            int response;
            do {
                std::cout << "Ваш ответ (1-4): ";
                std::cin >> response;

                if (std::cin.fail()) {
                    std::cin.clear();
                    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
                    std::cout << "Некорректный ввод! Пожалуйста, введите число от 1 до 4.\n";
                } else if (response < 1 || response > 4) {
                    std::cout << "Ошибка! Введите число от 1 до 4.\n";
                }

            } while (response < 1 || response > 4);
            answers[i] = response;
        }
    }

    void resultPrint(int result) {
        if (result < 30) {
            std::cout << "У вас низкая тревожность\n";
        }
        else if (result >= 31 && result < 46) {
            std::cout << "У вас средняя тревожность\n";
        }
        else {
            std::cout << "У вас высокая тревожность\n";
        }
    }

    virtual int calculateResult() = 0;
};



#endif //LAB_2_ANXIETYTEST_H
