#include "battery.h"
#include <iostream>
#include <windows.h>
#include <conio.h>
#include <initguid.h>
#include <batclass.h>

using namespace std;

namespace {
BatteryInfo g_previousInfo{};
bool g_firstCall = true;
int g_totalCapacity = 0;

string acLineStatusToString(BYTE status) {
    switch (status) {
    case 0: return "battery";
    case 1: return "mains";
    default: return "unknown";
    }
}

string batteryFlagToString(BYTE flag) {
    if (flag & 8) return "charging";
    if (flag & 2) return "discharging";
    if (flag & 1) return "high";
    if (flag & 4) return "low";
    if (flag & 128) return "critical";
    return "unknown";
}

string savingModeToString(BYTE reserved) {
    return reserved ? "on" : "off";
}

int calculateBatteryLife(const SYSTEM_POWER_STATUS &status, const BatteryInfo &prev) {
    if (g_firstCall) {
        g_firstCall = false;
        if (status.ACLineStatus == 0 && status.BatteryLifePercent > 0) {
            g_totalCapacity = status.BatteryLifeTime * 100 / status.BatteryLifePercent;
            return status.BatteryLifeTime;
        }
        if (status.ACLineStatus == 1) {
            g_totalCapacity = 34329;
            return status.BatteryLifePercent * g_totalCapacity / 100;
        }
    }

    if (prev.powerSupply == "battery" && status.ACLineStatus == 1 &&
        prev.lifeTime > 0 && prev.percentage > 0) {
        g_totalCapacity = prev.lifeTime * 100 / prev.percentage;
    }

    if (status.ACLineStatus == 1 && g_totalCapacity > 0) {
        return status.BatteryLifePercent * g_totalCapacity / 100;
    }

    return status.BatteryLifeTime;
}
}

Battery::Battery() = default;

string Battery::getBatteryChemistry() {
    HDEVINFO deviceInfoSet = SetupDiGetClassDevs(
        &GUID_DEVICE_BATTERY, nullptr, nullptr,
        DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
        );

    if (deviceInfoSet == INVALID_HANDLE_VALUE) return "unknown";

    SP_DEVICE_INTERFACE_DATA ifaceData{};
    ifaceData.cbSize = sizeof(ifaceData);

    if (!SetupDiEnumDeviceInterfaces(deviceInfoSet, nullptr, &GUID_DEVICE_BATTERY, 0, &ifaceData)) {
        SetupDiDestroyDeviceInfoList(deviceInfoSet);
        return "unknown";
    }

    DWORD requiredSize = 0;
    SetupDiGetDeviceInterfaceDetail(deviceInfoSet, &ifaceData, nullptr, 0, &requiredSize, nullptr);

    auto detailData = (PSP_DEVICE_INTERFACE_DETAIL_DATA)LocalAlloc(LPTR, requiredSize);
    if (!detailData) {
        SetupDiDestroyDeviceInfoList(deviceInfoSet);
        return "unknown";
    }
    detailData->cbSize = sizeof(*detailData);

    if (!SetupDiGetDeviceInterfaceDetail(deviceInfoSet, &ifaceData, detailData, requiredSize, &requiredSize, nullptr)) {
        LocalFree(detailData);
        SetupDiDestroyDeviceInfoList(deviceInfoSet);
        return "unknown";
    }

    HANDLE hBattery = CreateFile(
        detailData->DevicePath, GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL, nullptr
        );

    LocalFree(detailData);
    if (hBattery == INVALID_HANDLE_VALUE) {
        SetupDiDestroyDeviceInfoList(deviceInfoSet);
        return "unknown";
    }

    BATTERY_QUERY_INFORMATION queryInfo{};
    DWORD wait = 0, returned = 0;

    if (!DeviceIoControl(hBattery, IOCTL_BATTERY_QUERY_TAG, &wait, sizeof(wait),
                         &queryInfo.BatteryTag, sizeof(queryInfo.BatteryTag),
                         &returned, nullptr) || !queryInfo.BatteryTag) {
        CloseHandle(hBattery);
        SetupDiDestroyDeviceInfoList(deviceInfoSet);
        return "unknown";
    }

    BATTERY_INFORMATION batteryInfo{};
    queryInfo.InformationLevel = BatteryInformation;

    if (!DeviceIoControl(hBattery, IOCTL_BATTERY_QUERY_INFORMATION, &queryInfo, sizeof(queryInfo),
                         &batteryInfo, sizeof(batteryInfo), &returned, nullptr)) {
        CloseHandle(hBattery);
        SetupDiDestroyDeviceInfoList(deviceInfoSet);
        return "unknown";
    }

    CloseHandle(hBattery);
    SetupDiDestroyDeviceInfoList(deviceInfoSet);

    return string(reinterpret_cast<char*>(batteryInfo.Chemistry), 4);
}

BatteryInfo Battery::getBatteryInfo() {
    SYSTEM_POWER_STATUS status{};
    GetSystemPowerStatus(&status);

    BatteryInfo info;
    info.powerSupply   = acLineStatusToString(status.ACLineStatus);
    info.stateOfCharge = batteryFlagToString(status.BatteryFlag);
    info.percentage    = status.BatteryLifePercent;
    info.savingMode    = savingModeToString(status.Reserved1);
    info.lifeTime      = calculateBatteryLife(status, g_previousInfo);
    info.chemistry     = getBatteryChemistry();

    g_previousInfo = info;
    return info;
}

void Battery::printBatteryInfo() {
    auto info = getBatteryInfo();

    cout << "Power supply: "   << info.powerSupply   << "\n"
         << "State of charge: " << info.stateOfCharge << "\n"
         << "Percentage: "      << info.percentage    << "%\n"
         << "Saving mode: "     << info.savingMode    << "\n";

    if (info.lifeTime == -1) {
        cout << "Life time: calculating...\n";
    } else {
        int h = info.lifeTime / 3600;
        int m = (info.lifeTime % 3600) / 60;
        int s = info.lifeTime % 60;

        cout << "Life time: ";
        if (h > 0) cout << h << "h ";
        if (m > 0) cout << m << "m ";
        cout << s << "s\n";
    }

    cout << "Battery type: " << info.chemistry << "\n";

    static int debugCounter = 0;
    if (debugCounter++ % 10 == 0) {
        cout << "[Debug] Previous: " << g_previousInfo.powerSupply
             << ", " << g_previousInfo.percentage << "%\n";
    }
}
