//
// Created by atyme on 30.10.2024.
//

#ifndef LAB_2_SITUATIONALANXIETY_H
#define LAB_2_SITUATIONALANXIETY_H

#include <iostream>
#include "../header/AnxietyTest.h"

class SituationalAnxietyTest : public AnxietyTest {
public:
    SituationalAnxietyTest(int numQuestions, const std::vector<std::string>& questions)
            : AnxietyTest(numQuestions, questions) {}

    int calculateResult() override {
        int positiveSum = answers[2] + answers[3] + answers[5] + answers[6] + answers[8] + answers[11] + answers[12] + answers[13] + answers[16] + answers[17];
        int negativeSum = answers[0] + answers[1] + answers[4] + answers[7] + answers[9] + answers[10] + answers[14] + answers[15] + answers[18] + answers[19];
        int result = positiveSum - negativeSum + 50;
        return result;
    }
};


#endif //LAB_2_SITUATIONALANXIETY_H
