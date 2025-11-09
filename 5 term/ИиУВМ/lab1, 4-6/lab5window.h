#ifndef LAB5WINDOW_H
#define LAB5WINDOW_H

#include <QMainWindow>
#include <QTextEdit>
#include <QPushButton>
#include <QComboBox>
#include <QLabel>
#include <QTimer>
#include <QThread>
#include <QMutex>
#include <QTime>
#include <QScrollBar>
#include <QCloseEvent>
#include <QMessageBox>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGroupBox>
#include <QDebug>
#include <map>
#include <string>

// Предварительное объявление Windows типов
typedef unsigned long DWORD;

class UsbMonitorThread;

class Lab5Window : public QMainWindow
{
    Q_OBJECT

public:
    explicit Lab5Window(QWidget *parent = nullptr);
    ~Lab5Window();

signals:
    void backToMain();
    void usbDeviceConnected(const QString &deviceInfo);
    void usbDeviceDisconnected(const QString &deviceInfo);
    void usbDeviceListUpdated(const QStringList &devices);

protected:
    void closeEvent(QCloseEvent *event) override;

private slots:
    void onBackClicked();
    void onSafeUnmountClicked();
    void onUnsafeUnmountClicked();
    void onRefreshClicked();
    void onUsbDeviceConnected(const QString &deviceInfo);
    void onUsbDeviceDisconnected(const QString &deviceInfo);
    void onUsbDeviceListUpdated(const QStringList &devices);

private:
    void setupUI();
    void startUsbMonitoring();
    void stopUsbMonitoring();

    QTextEdit *outputTextEdit;
    QComboBox *deviceComboBox;
    QPushButton *safeUnmountButton;
    QPushButton *unsafeUnmountButton;
    QPushButton *refreshButton;
    QPushButton *backButton;
    QLabel *statusLabel;

    UsbMonitorThread *usbMonitorThread;
    QTimer *statusTimer;
};

// Поток для мониторинга USB
class UsbMonitorThread : public QThread
{
    Q_OBJECT

public:
    explicit UsbMonitorThread(QObject *parent = nullptr);
    ~UsbMonitorThread();

    void stopMonitoring();
    QString ejectDevice(const QString &deviceName);

signals:
    void deviceConnected(const QString &deviceInfo);
    void deviceDisconnected(const QString &deviceInfo);
    void deviceListUpdated(const QStringList &devices);

protected:
    void run() override;

private:
    bool m_stopMonitoring;
    QMutex m_mutex;

    void checkUsbDevices();
    int enumerateUsbDevices(bool printInfo = false, bool updateList = false);
    QString simulateEjectDevice(const QString &deviceName, bool safeEject);
    std::map<std::wstring, std::wstring> m_previousDevices;
    std::map<std::wstring, std::wstring> m_currentDevices;
    std::map<std::wstring, DWORD> m_deviceInstances;
};

#endif // LAB5WINDOW_H
