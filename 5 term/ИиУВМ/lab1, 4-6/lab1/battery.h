#ifndef BATTERY_H
#define BATTERY_H

#include <string>
#include <windows.h>
#include <setupapi.h>
#include <batclass.h>


// Определяем константу если она не определена
#ifndef BATTERY_LIFE_UNKNOWN
#define BATTERY_LIFE_UNKNOWN ((DWORD)0xFFFFFFFF)
#endif

struct BatteryInfo {
    std::string powerSupply;
    std::string stateOfCharge;
    int percentage;
    std::string savingMode;
    int lifeTime;
    std::string chemistry;
};

class Battery {
public:
    Battery();

    static BatteryInfo getBatteryInfo();
    static void printBatteryInfo();
    static char readKey();

private:
    static std::string getPowerSupply(SYSTEM_POWER_STATUS status);
    static std::string getStateCharge(SYSTEM_POWER_STATUS status);
    static std::string getSavingMode(SYSTEM_POWER_STATUS status);
    static int getBatteryLifeTime(SYSTEM_POWER_STATUS status, BatteryInfo& previousInfo);
    static std::string getBatteryChemistry();
};

#endif // BATTERY_H
