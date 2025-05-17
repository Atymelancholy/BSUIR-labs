#include <iostream>
#include <vector>
#include <string>
#include <limits>
#include <fstream>
#include <sstream>
#include <unordered_map>
#include "../header/AnxietyTest.h"
#include "../header/AnxietyCopingSuggestions.h"
#include "../header/UserManager.h"
#include "../header/SituationalAnxietyTest.h"
#include "../header/PersonalAnxietyTest.h"
#include "../header/globalFuncs.h"

using std::cout;
using std::cin;
using std::endl;

int main() {
    system("chcp 65001");
    UserManager userManager;
    int choice;

    cout << "Добро пожаловать в тест на тревожность!\n";
    cout << "1. Регистрация\n2. Вход\nВыберите действие: ";
    cin >> choice;
    cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

    if (choice == 1) {
        handleRegistration(userManager);
    } else if (choice == 2) {
        std::string username;
        if (!handleLogin(userManager, username)) {
            return 0;
        }
        handleUserActions(userManager, username);
    } else {
        cout << "Некорректный выбор.\n";
    }

    return 0;
}
