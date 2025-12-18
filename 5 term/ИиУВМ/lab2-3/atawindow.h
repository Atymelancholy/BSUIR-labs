#ifndef ATAWINDOW_H
#define ATAWINDOW_H

#include <QWidget>

class QTextEdit;
class QLabel;

class ATAWindow : public QWidget
{
    Q_OBJECT

public:
    explicit ATAWindow(QWidget *parent = 0);
    ~ATAWindow();

signals:
    void backToMainMenu();

public slots:
    void onGoBack();
    void onScanATA();

private:
    void initializeUI();
    void setupHeaderSection();
    void setupInfoSection();
    void setupResultsSection();
    void setupStatusSection();
    void applyStyles();

    bool waitReady(int channelNum);
    void waitDeviceBusy(int channelNum);
    bool getDeviceInfo(int devNum, int channelNum);
    void scanAllDevices();
    void displayDeviceInfo();
    QString extractString(int startIndex, int endIndex);
    QString getManufacturer();
    QString getInterfaceType();
    QString getSupportedModes();
    QString getDeviceType();
    void getRealDiskSpaceInfo();

    unsigned short ataData[256];

    static const int dataRegister[2];
    static const int deviceHeadRegister[2];
    static const int commandStatusRegister[2];
    static const int alternateStateRegister[2];

    #define IDENTIFY_DEVICE        0xEC
    #define IDENTIFY_PACKET_DEVICE 0xA1

    QTextEdit *m_resultsText;
    QLabel *m_statusLabel;

    QString m_model;
    QString m_manufacturer;
    QString m_serial;
    QString m_firmware;
    QString m_interface;
    QString m_supportedModes;
    QString m_deviceType;
    unsigned long long m_totalSectors;
    unsigned long long m_totalBytes;
    unsigned long long m_freeBytes;
    unsigned long long m_usedBytes;
    bool m_deviceFound;
};

#endif
