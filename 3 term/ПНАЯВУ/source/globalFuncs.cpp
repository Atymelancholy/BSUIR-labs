#include "../header/globalFuncs.h"
#include "../header/SituationalAnxietyTest.h"
#include "../header/AnxietyCopingSuggestions.h"
#include "../header/PersonalAnxietyTest.h"
#include "../header/UserManager.h"
#include <iostream>
#include <limits>
#include <vector>

using namespace std;

std::vector<std::string> getQuestions(const std::string& testType) {
    if (testType == "situational") {
        return {
                "Вы спокойны", "Вам ничто не угрожает", "Вы находитесь в напряжении",
                "Вы испытываете сожаление", "Вы чувствуете себя свободно",
                "Вы расстроены", "Вас волнуют возможные неудачи",
                "Вы чувствуете себя отдохнувшим человеком", "Вы встревожены",
                "Вы испытываете чувство внутреннего удовлетворения", "Вы уверены в себе",
                "Вы нервничаете", "Вы не находите себе места", "Вы взвинчены",
                "Вы не чувствуете скованности и напряжения", "Вы довольны",
                "Вы озабочены", "Вы слишком возбуждены", "Вам радостно", "Вам приятно"
        };
    } else if (testType == "personal") {
        return {
                "Вы испытываете удовольствие", "Вы быстро устаете",
                "Вы легко можете заплакать", "Вы хотели бы быть таким же счастливым человеком, как и другие",
                "Бывает, что вы проигрываете из-за того, что недостаточно быстро принимаете решения",
                "Вы чувствуете себя бодрым человеком", "Вы спокойны и собраны",
                "Ожидание трудностей очень тревожит вас", "Вы слишком переживаете из-за пустяков",
                "Вы бываете вполне счастливы", "Вы принимаете все слишком близко к сердцу",
                "Вам не хватает уверенности в себе", "Вы чувствуете себя в безопасности",
                "Вы стараетесь избегать критических ситуаций и трудностей",
                "У вас бывает хандра, тоска", "Вы бываете довольны",
                "Всякие пустяки отвлекают и волнуют вас",
                "Вы так сильно переживаете свои разочарования, что потом долго не можете о них забыть",
                "Вы уравновешенный человек", "Вас охватывает сильное беспокойство, когда вы думаете о своих делах и заботах"
        };
    } else {
        return {};
    }
}

void handleRegistration(UserManager& userManager) {
    std::string username, password;

    cout << "Введите имя пользователя: ";
    std::getline(cin, username);
    cout << "Введите пароль (8 символов): ";
    std::getline(cin, password);

    if (password.length() != 8) {
        cout << "Пароль должен содержать ровно 8 символов.\n";
        return;
    }

    userManager.registerUser(username, password);
};

bool handleLogin(UserManager& userManager, std::string& username) {
    std::string password;

    cout << "Введите имя пользователя: ";
    std::getline(cin, username);
    cout << "Введите пароль: ";
    std::getline(cin, password);
    return userManager.loginUser(username, password);
}

void handleTesting(UserManager& userManager, const std::string& username) {
    const int numQuestions = 20;
    std::vector<std::string> situationalQuestions = getQuestions("situational");
    std::vector<std::string> personalQuestions = getQuestions("personal");

    SituationalAnxietyTest situationalTest(numQuestions, situationalQuestions);
    cout << "Тест на ситуативную тревожность:\n";
    situationalTest.takeTest();
    int situationalScore = situationalTest.calculateResult();
    situationalTest.resultPrint(situationalScore);

    PersonalAnxietyTest personalTest(numQuestions, personalQuestions);
    cout << "\nТест на личностную тревожность:\n";
    personalTest.takeTest();
    int personalScore = personalTest.calculateResult();
    personalTest.resultPrint(personalScore);

    AnxietyCopingSuggestions suggestions(numQuestions, situationalQuestions);
    cout << "\nРекомендации по ситуативной тревожности:\n";
    suggestions.provideSuggestions(situationalScore);

    cout << "\nРекомендации по личностной тревожности:\n";
    suggestions.provideSuggestions(personalScore);

    userManager.saveTestResult(username, situationalScore, personalScore);
    userManager.compareResults(username, situationalScore, personalScore);
}

void handleUserActions(UserManager& userManager, const std::string& username) {
    cout << "\nЧто вы хотите сделать?\n1. Пройти тест\n2. Просмотреть историю тестов\nВыберите действие: ";
    int action;
    cin >> action;
    cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

    if (action == 1) {
        handleTesting(userManager, username);
    } else if (action == 2) {
        userManager.viewTestHistory(username);
    }
}