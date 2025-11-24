#ifndef LAB6WINDOW_H
#define LAB6WINDOW_H

#include <QMainWindow>
#include <QListWidget>
#include <QPushButton>
#include <QTextEdit>
#include <QProgressBar>
#include <QLabel>
#include <QGroupBox>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QSystemTrayIcon>
#include <QTimer>
#include <QProcess>
#include <QFile>
#include <atomic>
#include <thread>

#include <winsock2.h>
#include <ws2bth.h>
#include <bluetoothapis.h>

#pragma comment(lib, "Ws2_32.lib")
#pragma comment(lib, "Bthprops.lib")

class CharacterAnimation;

class Lab6Window : public QMainWindow
{
    Q_OBJECT

public:
    explicit Lab6Window(QWidget *parent = nullptr);
    ~Lab6Window();

signals:
    void backToMain();

private slots:
    void onScanDevicesClicked();
    void onSendFileClicked();
    void onReceiveFileClicked();
    void onBackClicked();
    void onDeviceSelected(QListWidgetItem* item);
    void updateBluetoothStatus();

protected:
    void closeEvent(QCloseEvent *event) override;
    void resizeEvent(QResizeEvent *event) override;
    void showEvent(QShowEvent *event) override;

private:
    QWidget *m_centralWidget;
    QGroupBox *m_devicesGroup;
    QGroupBox *m_transferGroup;
    QGroupBox *m_logGroup;
    QListWidget *m_devicesList;
    QPushButton *m_scanButton;
    QPushButton *m_sendButton;
    QPushButton *m_receiveButton;
    QPushButton *m_backButton;
    QTextEdit *m_logText;
    QProgressBar *m_progressBar;
    QLabel *m_statusLabel;

    CharacterAnimation *m_characterAnimation;
    QSystemTrayIcon *m_trayIcon;
    QTimer *m_statusTimer;

    std::atomic<bool> m_isScanning;
    std::atomic<bool> m_isTransferring;
    std::atomic<bool> m_isReceiving;
    std::thread* m_scanThread;
    std::thread* m_transferThread;
    std::thread* m_serverThread;

    SOCKET m_serverSocket;
    SOCKET m_clientSocket;

    QString m_selectedDevice;
    BTH_ADDR m_selectedDeviceAddr;
    QString m_receivedFilePath;

    void initializeUI();
    void setupConnections();
    void applyStyles();
    void initializeCharacterAnimation();
    void updateAnimationPosition();
    void startConnectionAnimation();
    void startTransferAnimation();
    void stopTransferAnimation();

    void scanBluetoothDevices();
    void startBluetoothServer();
    void stopBluetoothServer();
    bool sendFile(const QString& filePath);
    bool receiveFile();
    bool autoPlayFile(const QString& filePath);

    bool sendFileWithProtocol(const QString& filePath);
    bool receiveFileWithProtocol();
    bool detectFileTypeAndRename(const QString& filePath);

    void logMessage(const QString &message);
    void updateProgress(int value);
    void centerWindow();
    void showBluetoothAnimation(bool show);

    bool isBluetoothEnabled();
    QString getBluetoothRadioInfo();
    QVector<BLUETOOTH_DEVICE_INFO> enumerateBluetoothDevices();
    bool connectToDevice(BTH_ADDR deviceAddr);
};

#endif
