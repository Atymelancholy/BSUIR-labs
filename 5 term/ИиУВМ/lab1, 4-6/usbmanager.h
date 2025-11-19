// usbmanager.h
#ifndef USBMANAGER_H
#define USBMANAGER_H

#include <QObject>
#include <QTimer>
#include <windows.h>
#include <setupapi.h>
#include <cfgmgr32.h>
#include <map>
#include <string>
#include <memory>

class USBManager : public QObject
{
    Q_OBJECT

public:
    explicit USBManager(QObject *parent = nullptr);
    ~USBManager();

    struct USBDeviceInfo {
        std::wstring name;
        std::wstring vendorId;
        std::wstring deviceId;
        std::wstring manufacturer;
        DWORD devInst;

        bool operator==(const USBDeviceInfo& other) const {
            return vendorId == other.vendorId && deviceId == other.deviceId;
        }
    };

    using DeviceMap = std::map<std::wstring, USBDeviceInfo>;

    DeviceMap getDevices() const;
    bool ejectDevice(const std::wstring& deviceId);
    void refreshDevices();

public slots:
    void startMonitoring();
    void stopMonitoring();

signals:
    void devicesUpdated();
    void deviceConnected(const QString& deviceName);
    void deviceDisconnected(const QString& deviceName);
    void ejectionResult(const QString& message);

private slots:
    void onMonitoringTimeout();

private:
    struct EjectionResult {
        bool success;
        QString message;
        CONFIGRET errorCode;
    };

    class DeviceInfoSetHandle {
    public:
        DeviceInfoSetHandle(HDEVINFO handle) : m_handle(handle) {}
        ~DeviceInfoSetHandle() {
            if (m_handle && m_handle != INVALID_HANDLE_VALUE) {
                SetupDiDestroyDeviceInfoList(m_handle);
            }
        }
        operator HDEVINFO() const { return m_handle; }

    private:
        HDEVINFO m_handle;
    };

    enum class MonitoringState {
        Running,
        Stopped
    };

    DeviceMap enumerateDevices();
    bool populateDeviceInfo(HDEVINFO deviceInfoSet, SP_DEVINFO_DATA& deviceInfoData, USBDeviceInfo& result);
    std::wstring extractVendorId(const std::wstring& deviceIdStr);
    std::wstring extractDeviceId(const std::wstring& deviceIdStr);
    void detectDeviceChanges(const DeviceMap& oldDevices, const DeviceMap& newDevices);
    EjectionResult executeDeviceEjection(const USBDeviceInfo& deviceInfo);

    static CONFIGRET ejectVolume(DEVINST devInst);
    static bool isUSBDevice(const std::wstring& deviceId);

    DeviceMap m_devices;
    MonitoringState m_monitoringState;
    QTimer* m_monitoringTimer;
};

#endif // USBMANAGER_H
