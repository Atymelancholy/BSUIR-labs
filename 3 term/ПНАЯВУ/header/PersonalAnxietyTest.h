//
// Created by atyme on 30.10.2024.
//

#ifndef LAB_2_PERSONALANXIETY_H
#define LAB_2_PERSONALANXIETY_H

#include <iostream>

class PersonalAnxietyTest : public AnxietyTest {
public:
    PersonalAnxietyTest(int numQuestions, const std::vector<std::string>& questions)
            : AnxietyTest(numQuestions, questions) {}

    int calculateResult() override {
        int positiveSum = answers[1] + answers[2] + answers[3] + answers[4] + answers[7] + answers[10] + answers[11] + answers[13] + answers[14] + answers[16] + answers[17] + answers[19];
        int negativeSum = answers[0] + answers[5] + answers[6] + answers[9] + answers[12] + answers[15] + answers[18];
        int result = positiveSum - negativeSum + 35;
        return result;
    }
};


#endif //LAB_2_PERSONALANXIETY_H
