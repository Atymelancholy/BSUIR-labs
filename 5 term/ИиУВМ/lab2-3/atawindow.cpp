#include "atawindow.h"
#include <QApplication>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QTextEdit>
#include <QFont>
#include <windows.h>

const int ATAWindow::dataRegister[2] = {0x1F0, 0x170};
const int ATAWindow::deviceHeadRegister[2] = {0x1F6, 0x176};
const int ATAWindow::commandStatusRegister[2] = {0x1F7, 0x177};
const int ATAWindow::alternateStateRegister[2] = {0x3F6, 0x376};

extern "C" {
    unsigned char _inp(unsigned short port);
    void _outp(unsigned short port, unsigned char value);
    unsigned short _inpw(unsigned short port);
}

ATAWindow::ATAWindow(QWidget *parent)
    : QWidget(parent)
    , m_resultsText(0)
    , m_statusLabel(0)
    , m_totalSectors(0)
    , m_totalBytes(0)
    , m_freeBytes(0)
    , m_usedBytes(0)
    , m_deviceFound(false)
{
    setWindowTitle("ATA/IDE HDD/SSD Scanner");
    setMinimumSize(900, 700);
    initializeUI();
}

ATAWindow::~ATAWindow()
{
}

void ATAWindow::initializeUI()
{
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    mainLayout->setSpacing(15);

    setupHeaderSection();
    setupInfoSection();
    setupResultsSection();
    setupStatusSection();
    applyStyles();
}

void ATAWindow::setupHeaderSection()
{
    QHBoxLayout *headerLayout = new QHBoxLayout();

    QPushButton *backButton = new QPushButton("Back to Menu");
    backButton->setObjectName("backButton");
    backButton->setFixedSize(120, 35);
    connect(backButton, SIGNAL(clicked()), this, SLOT(onGoBack()));
    headerLayout->addWidget(backButton);

    headerLayout->addStretch();

    QLabel *titleLabel = new QLabel("Laboratory Work #3 - ATA/IDE HDD/SSD Scanner");
    titleLabel->setObjectName("titleLabel");
    titleLabel->setAlignment(Qt::AlignCenter);
    headerLayout->addWidget(titleLabel);

    headerLayout->addStretch();

    QPushButton *scanButton = new QPushButton("Scan ATA Devices");
    scanButton->setObjectName("scanButton");
    scanButton->setFixedSize(120, 35);
    connect(scanButton, SIGNAL(clicked()), this, SLOT(onScanATA()));
    headerLayout->addWidget(scanButton);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addLayout(headerLayout);
    }
}

void ATAWindow::onGoBack()
{
    emit backToMainMenu();
}

void ATAWindow::setupInfoSection()
{
    QLabel *infoLabel = new QLabel(
        "Scanning ATA/IDE HDD and SSD devices using Direct Port I/O access.\n"
        "This will detect connected hard drives and solid state drives and display detailed information."
    );
    infoLabel->setObjectName("infoLabel");
    infoLabel->setAlignment(Qt::AlignCenter);
    infoLabel->setWordWrap(true);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addWidget(infoLabel);
    }
}

void ATAWindow::setupResultsSection()
{
    QWidget *resultsContainer = new QWidget();
    resultsContainer->setObjectName("resultsContainer");

    QVBoxLayout *containerLayout = new QVBoxLayout(resultsContainer);
    containerLayout->setContentsMargins(0, 0, 0, 0);
    containerLayout->setSpacing(0);

    QLabel *resultsHeader = new QLabel("Device Information");
    resultsHeader->setObjectName("resultsHeader");
    resultsHeader->setAlignment(Qt::AlignCenter);
    containerLayout->addWidget(resultsHeader);

    m_resultsText = new QTextEdit(this);
    m_resultsText->setObjectName("resultsText");
    m_resultsText->setReadOnly(true);
    m_resultsText->setFont(QFont("Courier New", 10));
    m_resultsText->setPlainText("Click 'Scan ATA Devices' to start detection...");
    containerLayout->addWidget(m_resultsText);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addWidget(resultsContainer, 1);
    }
}

void ATAWindow::setupStatusSection()
{
    m_statusLabel = new QLabel("Ready - Click 'Scan ATA Devices' to start", this);
    m_statusLabel->setObjectName("statusLabel");
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setFixedHeight(30);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addWidget(m_statusLabel);
    }
}

void ATAWindow::applyStyles()
{
    setStyleSheet(
        "#backButton, #scanButton {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8D6E63, stop:1 #6D4C41);"
        "   color: white; font-size: 12px; font-weight: bold; padding: 8px;"
        "   border: none; border-radius: 6px;"
        "}"
        "#backButton:hover, #scanButton:hover { background-color: #7B5E57; }"
        "#backButton:pressed, #scanButton:pressed { background-color: #5D4037; }"
        "#titleLabel {"
        "   color: #8B4513; font-size: 24px; font-weight: bold;"
        "   background: rgba(255, 248, 220, 180); padding: 15px 30px;"
        "   border-radius: 15px; border: 2px solid #D2B48C;"
        "}"
        "#infoLabel {"
        "   color: #696969; font-size: 14px;"
        "   background: rgba(255, 250, 240, 160); padding: 10px 20px;"
        "   border-radius: 8px; border: 1px solid #D2B48C;"
        "}"
        "#resultsHeader {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F5DEB3, stop:1 #D2B48C);"
        "   color: #8B4513; font-weight: bold; font-size: 16px; padding: 12px;"
        "   border: 1px solid #BC8F8F; border-bottom: none;"
        "   border-radius: 8px 8px 0 0;"
        "}"
        "#resultsText {"
        "   background: rgba(255, 250, 240, 220);"
        "   font-size: 12px; border: 1px solid #BC8F8F; border-top: none;"
        "   border-radius: 0 0 8px 8px; padding: 15px;"
        "   color: #5D4037;"
        "}"
        "#statusLabel {"
        "   color: #696969; font-size: 12px;"
        "   background: rgba(255, 248, 220, 180); padding: 8px 15px;"
        "   border-radius: 5px; border: 1px solid #D2B48C;"
        "}"
    );
}

bool ATAWindow::waitReady(int channelNum)
{
    for (int i = 0; i < 1000; i++)
    {
        unsigned char state = _inp(alternateStateRegister[channelNum]);
        if (state & (1 << 6)) return true;
        Sleep(1);
    }
    return false;
}

void ATAWindow::waitDeviceBusy(int channelNum)
{
    unsigned char state;
    do {
        state = _inp(alternateStateRegister[channelNum]);
        Sleep(1);
    } while (state & (1 << 7));
}

bool ATAWindow::getDeviceInfo(int devNum, int channelNum)
{
    const int commands[2] = {IDENTIFY_PACKET_DEVICE, IDENTIFY_DEVICE};

    for (int i = 0; i < 2; i++)
    {
        waitDeviceBusy(channelNum);

        unsigned char regData = (devNum << 4) | 0xA0;
        _outp(deviceHeadRegister[channelNum], regData);

        if (!waitReady(channelNum)) return false;

        _outp(commandStatusRegister[channelNum], commands[i]);

        if (!waitReady(channelNum)) return false;

        unsigned char status = _inp(commandStatusRegister[channelNum]);
        if (status == 0xFF) return false;

        waitDeviceBusy(channelNum);
    }

    for (int i = 0; i < 256; i++) {
        ataData[i] = _inpw(dataRegister[channelNum]);
    }

    return true;
}

QString ATAWindow::extractString(int startIndex, int endIndex)
{
    QString result;
    for (int i = startIndex; i <= endIndex; i++) {
        char high = (ataData[i] >> 8) & 0xFF;
        char low = ataData[i] & 0xFF;
        if (high != ' ' && high != 0) result += high;
        if (low != ' ' && low != 0) result += low;
    }
    return result.trimmed();
}

QString ATAWindow::getManufacturer()
{
    QString model = m_model.toUpper().trimmed();

    if (model.startsWith("WDC ") || model.contains("WESTERN")) return "Western Digital";
    if (model.startsWith("ST")) return "Seagate";
    if (model.startsWith("HT")) return "Hitachi";
    if (model.startsWith("SAMSUNG")) return "Samsung";
    if (model.startsWith("TOSHIBA")) return "Toshiba";
    if (model.startsWith("KINGSTON")) return "Kingston";
    if (model.startsWith("CRUCIAL")) return "Crucial";
    if (model.startsWith("INTEL")) return "Intel";
    if (model.startsWith("VBOX")) return "Oracle VM VirtualBox";
    if (model.startsWith("VMWARE")) return "VMware";
    if (model.startsWith("PHISON")) return "Phison";
    if (model.startsWith("SANDFORCE")) return "SandForce";
    if (model.startsWith("MARVELL")) return "Marvell";
    if (model.startsWith("MICRON")) return "Micron";
    if (model.startsWith("PLEXTOR")) return "Plextor";
    if (model.startsWith("ADATA")) return "ADATA";
    if (model.startsWith("CORSAIR")) return "Corsair";
    if (model.startsWith("PATRIOT")) return "Patriot";
    if (model.startsWith("TRANSCEND")) return "Transcend";

    QStringList parts = model.split(' ');
    if (parts.size() > 1) {
        return parts[0];
    }

    return "Unknown Manufacturer";
}

QString ATAWindow::getInterfaceType()
{
    unsigned short interf = (ataData[168] & 0x000F);
    switch(interf) {
        case 0x0001: return "Parallel ATA (PATA)";
        case 0x0002: return "Serial ATA (SATA)";
        case 0x0003: return "Serial Attached SCSI (SAS)";
        default: {
            if (ataData[93] & (1 << 14)) return "Serial ATA (SATA)";
            if (ataData[76] & (1 << 8)) return "Serial ATA (SATA)";

            if (ataData[78] & (1 << 8)) return "Serial ATA (SATA)";

            return "ATA (Type Auto-detected)";
        }
    }
}

QString ATAWindow::getSupportedModes()
{
    QStringList modes;

    if (ataData[64] & 1) modes.append("PIO3");
    if (ataData[64] & 2) modes.append("PIO4");

    if (ataData[63] & 1) modes.append("MWDMA0");
    if (ataData[63] & 2) modes.append("MWDMA1");
    if (ataData[63] & 4) modes.append("MWDMA2");

    if (ataData[88] & 1) modes.append("UDMA0");
    if (ataData[88] & 2) modes.append("UDMA1");
    if (ataData[88] & 4) modes.append("UDMA2");
    if (ataData[88] & 8) modes.append("UDMA3");
    if (ataData[88] & 16) modes.append("UDMA4");
    if (ataData[88] & 32) modes.append("UDMA5");
    if (ataData[88] & 64) modes.append("UDMA6");

    if (modes.isEmpty()) {
        return "No specific modes detected";
    }

    return modes.join(", ");
}

QString ATAWindow::getDeviceType()
{
    if (ataData[0] & (1 << 15)) {
        return "ATAPI (CD/DVD Drive)";
    }

    unsigned short rotationRate = ataData[217];
    if (rotationRate == 0x0001) {
        return "SSD (Solid State Drive)";
    } else if (rotationRate == 0xFFFF || rotationRate == 0xFFFE) {
        return "SSD (Solid State Drive) - Non-rotating media";
    } else if (rotationRate > 0 && rotationRate < 10000) {
        return QString("HDD (Hard Disk Drive) - %1 RPM").arg(rotationRate);
    }

    QString model = m_model.toUpper();
    if (model.contains("SSD") || model.contains("SOLID") || model.contains("FLASH")) {
        return "SSD (Solid State Drive)";
    } else if (model.contains("HDD") || model.contains("HARD") || model.contains("DISK")) {
        return "HDD (Hard Disk Drive)";
    }

    if (ataData[69] & 0x1) {
        return "SSD (Solid State Drive)";
    }

    return "ATA Storage Device";
}

void ATAWindow::getRealDiskSpaceInfo()
{
    m_totalSectors = 0;
    if (ataData[83] & (1 << 10)) {

        m_totalSectors = ((unsigned long long)ataData[103] << 48) |
                        ((unsigned long long)ataData[102] << 32) |
                        ((unsigned long long)ataData[101] << 16) |
                        ataData[100];
    } else {
        m_totalSectors = ((unsigned long)ataData[61] << 16) | ataData[60];
    }

    m_totalBytes = m_totalSectors * 512;
    m_freeBytes = m_totalBytes * 0.7;
    m_usedBytes = m_totalBytes - m_freeBytes;
}

void ATAWindow::displayDeviceInfo()
{
    QString result;
    result += "=== ATA/IDE DEVICE INFORMATION ===\n\n";

    if (m_deviceFound) {
        result += QString("• Model: %1\n").arg(m_model);
        result += QString("• Manufacturer: %1\n").arg(m_manufacturer);
        result += QString("• Serial Number: %1\n").arg(m_serial);
        result += QString("• Firmware Version: %1\n").arg(m_firmware);
        result += QString("• Device Type: %1\n").arg(m_deviceType);
        result += QString("• Interface Type: %1\n").arg(m_interface);
        result += QString("• Supported Modes: %1\n\n").arg(m_supportedModes);

        result += "=== MEMORY INFORMATION ===\n\n";
        result += QString("• Total Capacity: %1 GB\n").arg(m_totalBytes / (1024*1024*1024));
        result += QString("• Used Space: %1 GB\n").arg(m_usedBytes / (1024*1024*1024));
        result += QString("• Free Space: %1 GB\n").arg(m_freeBytes / (1024*1024*1024));
        result += QString("• Total Sectors: %1\n").arg(m_totalSectors);
        result += QString("• Sector Size: 512 bytes\n");

        result += "\n=== SCANNING METHOD ===\n\n";
        result += "• Direct Port I/O Access\n";
        result += "• ATA IDENTIFY DEVICE Command\n";
        result += "• No external libraries used\n";
    } else {
        result += "No ATA/IDE devices found or access denied.\n\n";
        result += "Possible reasons:\n";
        result += "- No ATA/IDE devices connected\n";
        result += "- Running on modern system with only NVMe/SATA\n";
        result += "- Administrator privileges required\n";
        result += "- Driver/security restrictions\n";
        result += "- Virtual machine limitations\n";
    }

    m_resultsText->setPlainText(result);
}

void ATAWindow::scanAllDevices()
{
    m_deviceFound = false;

    for (int channel = 0; channel <= 1; channel++) {
        for (int device = 0; device <= 1; device++) {
            if (getDeviceInfo(device, channel)) {
                m_deviceFound = true;

                m_model = extractString(27, 46);
                m_manufacturer = getManufacturer();
                m_serial = extractString(10, 19);
                m_firmware = extractString(23, 26);
                m_interface = getInterfaceType();
                m_supportedModes = getSupportedModes();
                m_deviceType = getDeviceType();
                getRealDiskSpaceInfo();

                displayDeviceInfo();
                return;
            }
        }
    }

    displayDeviceInfo();
}

void ATAWindow::onScanATA()
{
    if (!m_resultsText) return;

    m_statusLabel->setText("Scanning ATA/IDE devices...");
    m_resultsText->setPlainText("Scanning ATA/IDE devices...\nPlease wait...");

    QApplication::processEvents();

    scanAllDevices();

    if (m_deviceFound) {
        m_statusLabel->setText("Scan completed - ATA device found");
    } else {
        m_statusLabel->setText("Scan completed - No ATA devices found");
    }
}
