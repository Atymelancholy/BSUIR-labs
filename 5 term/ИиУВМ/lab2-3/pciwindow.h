#ifndef PCIWINDOW_H
#define PCIWINDOW_H

#include <QWidget>
#include <QTableWidget>
#include <QVBoxLayout>
#include <QPushButton>
#include <QLabel>
#include <QHBoxLayout>
#include <QPainter>

extern "C" {
#include "hexioctrl.h"
}

struct PCIDeviceInfo {
    int bus;
    int device;
    int function;
    unsigned long deviceID;
    unsigned long vendorID;
    unsigned long baseClass;
    unsigned long subClass;
    unsigned long progIf;
    unsigned long revisionID;
    unsigned long subsysID;
    unsigned long subsysVendID;
    QString vendorName;
    QString deviceName;
    QString className;
    QString devicePath;
};

class PCIWindow : public QWidget
{
    Q_OBJECT

public:
    explicit PCIWindow(QWidget *parent = 0);
    ~PCIWindow();

private slots:
    void onScanPCI();
    void onGoBack();

private:
    void initializeUI();
    void setupHeaderSection();
    void setupInfoSection();
    void setupTableSection();
    void setupStatusSection();
    void applyStyles();

    PCIDeviceInfo scanDevice(int bus, int device, int function);
    bool validateDevice(const PCIDeviceInfo& deviceInfo);
    void addDeviceToTable(const PCIDeviceInfo& deviceInfo);
    unsigned long readPCIConfig(int bus, int device, int function, int reg);
    unsigned long calculatePCIAddress(int bus, int device, int function, int reg);
    bool checkDeviceExists(int bus, int device, int function);
    void parseDeviceDetails(PCIDeviceInfo& deviceInfo);
    QString formatDevicePath(const PCIDeviceInfo& deviceInfo);
    void resolveDeviceNames(PCIDeviceInfo& deviceInfo);

    void clearLayout(QLayout* layout);
    QTableWidgetItem* createTableItem(const QString& text, Qt::Alignment alignment = Qt::AlignCenter);

    QTableWidget *m_table;
    QLabel *m_statusLabel;

protected:
    void paintEvent(QPaintEvent *event) override;

signals:
    void backToMainMenu();
};

#endif
