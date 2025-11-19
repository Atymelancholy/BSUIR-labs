#include "usbmanager.h"
#include <thread>
#include <chrono>
#include <QDebug>

#pragma comment(lib, "setupapi.lib")
#pragma comment(lib, "cfgmgr32.lib")

#ifndef GUID_DEVINTERFACE_USB_DEVICE
DEFINE_GUID(GUID_DEVINTERFACE_USB_DEVICE,
            0xA5DCBF10, 0x6530, 0x11D2, 0x90, 0x1F, 0x00, 0xC0, 0x4F, 0xB9, 0x51, 0xED);
#endif

namespace Constants {
constexpr int MONITORING_INTERVAL_MS = 2000;
constexpr int PROPERTY_BUFFER_SIZE = 1024;
constexpr int MAX_DEVICE_INSTANCE_ID_LENGTH = 200;
const std::wstring UNKNOWN_DEVICE = L"Unknown Device";
const std::wstring UNKNOWN_MANUFACTURER = L"Unknown Manufacturer";
const std::wstring UNKNOWN_ID = L"Unknown";
const std::wstring USB_PREFIX = L"USB\\";
const std::wstring VID_PREFIX = L"VID_";
const std::wstring PID_PREFIX = L"PID_";
constexpr size_t ID_LENGTH = 4;
}

USBManager::USBManager(QObject *parent)
    : QObject{parent}
    , m_monitoringState(MonitoringState::Stopped)
    , m_monitoringTimer(new QTimer(this))
{
    connect(m_monitoringTimer, &QTimer::timeout, this, &USBManager::onMonitoringTimeout);
    startMonitoring();
}

USBManager::~USBManager()
{
    stopMonitoring();
}

void USBManager::startMonitoring()
{
    if (m_monitoringState == MonitoringState::Running) {
        return;
    }

    m_monitoringTimer->start(Constants::MONITORING_INTERVAL_MS);
    m_monitoringState = MonitoringState::Running;
    qDebug() << "USB monitoring started";
}

void USBManager::stopMonitoring()
{
    m_monitoringTimer->stop();
    m_monitoringState = MonitoringState::Stopped;
    qDebug() << "USB monitoring stopped";
}

USBManager::DeviceMap USBManager::getDevices() const
{
    return m_devices;
}

void USBManager::refreshDevices()
{
    DeviceMap newDevices = enumerateDevices();
    detectDeviceChanges(m_devices, newDevices);
    m_devices = std::move(newDevices);
    emit devicesUpdated();
}

bool USBManager::ejectDevice(const std::wstring& deviceId)
{
    const auto deviceIt = m_devices.find(deviceId);
    if (deviceIt == m_devices.end()) {
        emit ejectionResult("Устройство не найдено");
        return false;
    }

    const EjectionResult result = executeDeviceEjection(deviceIt->second);
    emit ejectionResult(result.message);

    return result.success;
}

USBManager::EjectionResult USBManager::executeDeviceEjection(const USBDeviceInfo& deviceInfo)
{
    const CONFIGRET errorCode = ejectVolume(deviceInfo.devInst);

    switch (errorCode) {
    case CR_SUCCESS:
        return {true, "Устройство безопасно извлечено", errorCode};

    case CR_REMOVE_VETOED:
        return {false, "Устройство используется в данный момент", errorCode};

    case CR_NO_SUCH_DEVNODE:
        refreshDevices();
        return {false, "Устройство больше не существует", errorCode};

    default:
        return {false, QString("Ошибка извлечения устройства (код: %1)").arg(errorCode), errorCode};
    }
}

void USBManager::onMonitoringTimeout()
{
    refreshDevices();
}

USBManager::DeviceMap USBManager::enumerateDevices()
{
    DeviceMap devices;

    SP_DEVINFO_DATA deviceInfoData;
    ZeroMemory(&deviceInfoData, sizeof(deviceInfoData));
    deviceInfoData.cbSize = sizeof(deviceInfoData);

    DeviceInfoSetHandle deviceInfoSet(SetupDiGetClassDevsW(
        NULL, L"USB", NULL, DIGCF_PRESENT | DIGCF_ALLCLASSES));

    if (deviceInfoSet == INVALID_HANDLE_VALUE) {
        qWarning() << "Failed to get device list";
        return devices;
    }

    for (DWORD i = 0; SetupDiEnumDeviceInfo(deviceInfoSet, i, &deviceInfoData); i++) {
        USBDeviceInfo deviceInfo;

        if (populateDeviceInfo(deviceInfoSet, deviceInfoData, deviceInfo)) {
            std::wstring key = deviceInfo.vendorId + L"_" + deviceInfo.deviceId;
            devices[key] = std::move(deviceInfo);
        }
    }

    return devices;
}

bool USBManager::populateDeviceInfo(HDEVINFO deviceInfoSet, SP_DEVINFO_DATA& deviceInfoData, USBDeviceInfo& result)
{
    wchar_t deviceId[Constants::MAX_DEVICE_INSTANCE_ID_LENGTH];
    wchar_t deviceName[Constants::PROPERTY_BUFFER_SIZE];
    wchar_t manufacturer[Constants::PROPERTY_BUFFER_SIZE];

    ZeroMemory(deviceId, sizeof(deviceId));
    ZeroMemory(deviceName, sizeof(deviceName));
    ZeroMemory(manufacturer, sizeof(manufacturer));

    if (!SetupDiGetDeviceInstanceIdW(deviceInfoSet, &deviceInfoData,
                                     deviceId, sizeof(deviceId), NULL)) {
        return false;
    }

    if (!isUSBDevice(deviceId)) {
        return false;
    }

    DWORD dataType;
    if (!SetupDiGetDeviceRegistryPropertyW(deviceInfoSet, &deviceInfoData, SPDRP_DEVICEDESC,
                                           &dataType, reinterpret_cast<PBYTE>(deviceName),
                                           sizeof(deviceName), NULL)) {
        wcscpy(deviceName, Constants::UNKNOWN_DEVICE.c_str());
    }

    if (!SetupDiGetDeviceRegistryPropertyW(deviceInfoSet, &deviceInfoData, SPDRP_MFG,
                                           &dataType, reinterpret_cast<PBYTE>(manufacturer),
                                           sizeof(manufacturer), NULL)) {
        wcscpy(manufacturer, Constants::UNKNOWN_MANUFACTURER.c_str());
    }

    result.name = deviceName;
    result.vendorId = extractVendorId(deviceId);
    result.deviceId = extractDeviceId(deviceId);
    result.manufacturer = manufacturer;
    result.devInst = deviceInfoData.DevInst;

    return true;
}

std::wstring USBManager::extractVendorId(const std::wstring& deviceIdStr)
{
    size_t vidPos = deviceIdStr.find(Constants::VID_PREFIX);
    if (vidPos != std::wstring::npos) {
        return deviceIdStr.substr(vidPos + Constants::VID_PREFIX.length(), Constants::ID_LENGTH);
    }
    return Constants::UNKNOWN_ID;
}

std::wstring USBManager::extractDeviceId(const std::wstring& deviceIdStr)
{
    size_t pidPos = deviceIdStr.find(Constants::PID_PREFIX);
    if (pidPos != std::wstring::npos) {
        return deviceIdStr.substr(pidPos + Constants::PID_PREFIX.length(), Constants::ID_LENGTH);
    }
    return Constants::UNKNOWN_ID;
}

void USBManager::detectDeviceChanges(const DeviceMap& oldDevices, const DeviceMap& newDevices)
{
    for (const auto& [key, newDevice] : newDevices) {
        if (oldDevices.find(key) == oldDevices.end()) {
            emit deviceConnected(QString::fromWCharArray(newDevice.name.c_str()));
        }
    }

    for (const auto& [key, oldDevice] : oldDevices) {
        if (newDevices.find(key) == newDevices.end()) {
            emit deviceDisconnected(QString::fromWCharArray(oldDevice.name.c_str()));
        }
    }
}

CONFIGRET USBManager::ejectVolume(DEVINST devInst)
{
    return CM_Request_Device_EjectW(devInst, nullptr, nullptr, 0, 0);
}

bool USBManager::isUSBDevice(const std::wstring& deviceId)
{
    return deviceId.find(Constants::USB_PREFIX) != std::wstring::npos;
}
