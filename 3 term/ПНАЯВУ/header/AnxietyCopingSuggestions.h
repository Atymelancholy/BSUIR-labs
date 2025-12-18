//
// Created by atyme on 30.10.2024.
//

#ifndef LAB_2_ANXIETYCOPINGSUGGESTIONS_H
#define LAB_2_ANXIETYCOPINGSUGGESTIONS_H

#include "../header/AnxietyTest.h"
#include <iostream>
#include <vector>

class AnxietyCopingSuggestions : public AnxietyTest {
public:
    AnxietyCopingSuggestions(int numQuestions, const std::vector<std::string>& questions)
            : AnxietyTest(numQuestions, questions) {}

    void provideSuggestions(int score) {
        if (score >= 46) {
            std::cout << "Рекомендации по управлению высокой тревожностью:\n";
            std::cout << "- Попробуйте глубокое дыхание и техники медитации.\n";
            std::cout << "- Обратитесь к профессионалу, если чувствуете, что тревожность мешает вам.\n";
            std::cout << "- Разработайте регулярный режим сна и отдыха.\n";
        }
        else if (score >= 31) {
            std::cout << "Рекомендации по управлению средней тревожностью:\n";
            std::cout << "- Практикуйте физическую активность для снятия стресса.\n";
            std::cout << "- Старайтесь избегать перегрузки информацией.\n";
            std::cout << "- Используйте техники расслабления, такие как йога или расслабляющая музыка.\n";
        }
    }

    int calculateResult() override {
        return 0;
    }
};



#endif //LAB_2_ANXIETYCOPINGSUGGESTIONS_H
