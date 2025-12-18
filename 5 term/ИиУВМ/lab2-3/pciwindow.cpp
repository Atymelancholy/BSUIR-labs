#include "pciwindow.h"
#include <QHeaderView>
#include <QDebug>

extern "C" {
    #include "(PCI_DEVS)pci_codes.h"
}

namespace Colors {
    const QColor LightBeige(255, 235, 205);
    const QColor DarkBeige(210, 180, 140);
}

PCIWindow::PCIWindow(QWidget *parent)
    : QWidget(parent)
    , m_table(0)
    , m_statusLabel(0)
{
    setWindowTitle("PCI Configuration Space Scanner");
    ALLOW_IO_OPERATIONS;
    initializeUI();
    onScanPCI();
}

PCIWindow::~PCIWindow()
{
}

void PCIWindow::clearLayout(QLayout* layout)
{
    if (!layout) return;

    QLayoutItem* item;
    while ((item = layout->takeAt(0)) != 0) {
        if (QWidget* widget = item->widget()) {
            widget->deleteLater();
        }
        if (QLayout* childLayout = item->layout()) {
            clearLayout(childLayout);
        }
        delete item;
    }
}

void PCIWindow::initializeUI()
{
    clearLayout(layout());

    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    mainLayout->setSpacing(15);

    setupHeaderSection();
    setupInfoSection();
    setupTableSection();
    setupStatusSection();
    applyStyles();
}

void PCIWindow::setupHeaderSection()
{
    QHBoxLayout *headerLayout = new QHBoxLayout();

    QPushButton *backButton = new QPushButton("Back to Menu");
    backButton->setObjectName("backButton");
    backButton->setFixedSize(120, 35);
    connect(backButton, SIGNAL(clicked()), this, SLOT(onGoBack()));
    headerLayout->addWidget(backButton);

    headerLayout->addStretch();

    QLabel *titleLabel = new QLabel("Laboratory Work #2 - PCI Devices Scanner");
    titleLabel->setObjectName("titleLabel");
    titleLabel->setAlignment(Qt::AlignCenter);
    headerLayout->addWidget(titleLabel);

    headerLayout->addStretch();

    QWidget *spacer = new QWidget();
    spacer->setFixedSize(120, 35);
    headerLayout->addWidget(spacer);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addLayout(headerLayout);
    }
}
void PCIWindow::onGoBack()
{
    emit backToMainMenu();
}

void PCIWindow::setupInfoSection()
{
    QLabel *infoLabel = new QLabel(
        "Detected PCI devices on your system. Scanning using Direct Port I/O access."
    );
    infoLabel->setObjectName("infoLabel");
    infoLabel->setAlignment(Qt::AlignCenter);
    infoLabel->setWordWrap(true);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addWidget(infoLabel);
    }
}

void PCIWindow::setupTableSection()
{
    QWidget *tableContainer = new QWidget();
    tableContainer->setObjectName("tableContainer");

    QVBoxLayout *containerLayout = new QVBoxLayout(tableContainer);
    containerLayout->setContentsMargins(0, 0, 0, 0);
    containerLayout->setSpacing(0);

    QLabel *tableHeader = new QLabel("PCI Devices List");
    tableHeader->setObjectName("tableHeader");
    tableHeader->setAlignment(Qt::AlignCenter);
    containerLayout->addWidget(tableHeader);

    m_table = new QTableWidget(this);
    m_table->setObjectName("pciTable");
    m_table->setColumnCount(3);

    QStringList headers;
    headers << "Vendor ID" << "Device ID" << "Device Information";
    m_table->setHorizontalHeaderLabels(headers);

    m_table->setSelectionBehavior(QAbstractItemView::SelectRows);
    m_table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    m_table->setAlternatingRowColors(true);
    m_table->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    m_table->verticalHeader()->setVisible(false);
    m_table->horizontalHeader()->setStretchLastSection(true);
    m_table->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    m_table->setColumnWidth(0, 120);
    m_table->setColumnWidth(1, 120);

    containerLayout->addWidget(m_table);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addWidget(tableContainer, 1);
    }
}

void PCIWindow::setupStatusSection()
{
    m_statusLabel = new QLabel("Ready - PCI scan completed", this);
    m_statusLabel->setObjectName("statusLabel");
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setFixedHeight(30);

    QVBoxLayout *mainLayout = qobject_cast<QVBoxLayout*>(layout());
    if (mainLayout) {
        mainLayout->addWidget(m_statusLabel);
    }
}

void PCIWindow::applyStyles()
{
    setStyleSheet(
        "#backButton {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8D6E63, stop:1 #6D4C41);"
        "   color: white;"
        "   font-size: 12px;"
        "   font-weight: bold;"
        "   padding: 8px;"
        "   border: none;"
        "   border-radius: 6px;"
        "}"
        "#backButton:hover { background-color: #7B5E57; }"
        "#backButton:pressed { background-color: #5D4037; }"
        ""
        "#titleLabel {"
        "   color: #8B4513;"
        "   font-size: 28px;"
        "   font-weight: bold;"
        "   background: rgba(255, 248, 220, 180);"
        "   padding: 15px 30px;"
        "   border-radius: 15px;"
        "   border: 2px solid #D2B48C;"
        "}"
        "#titleLabel {"
        "   color: #8B4513;"
        "   font-size: 28px;"
        "   font-weight: bold;"
        "   background: rgba(255, 248, 220, 180);"
        "   padding: 15px 30px;"
        "   border-radius: 15px;"
        "   border: 2px solid #D2B48C;"
        "}"
        ""
        "#infoLabel {"
        "   color: #696969;"
        "   font-size: 14px;"
        "   background: rgba(255, 250, 240, 160);"
        "   padding: 10px 20px;"
        "   border-radius: 8px;"
        "   border: 1px solid #D2B48C;"
        "}"
        ""
        "#tableHeader {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F5DEB3, stop:1 #D2B48C);"
        "   color: #8B4513;"
        "   font-weight: bold;"
        "   font-size: 16px;"
        "   padding: 12px;"
        "   border: 1px solid #BC8F8F;"
        "   border-bottom: none;"
        "   border-radius: 8px 8px 0 0;"
        "}"
        ""
        "#pciTable {"
        "   background: rgba(255, 250, 240, 220);"
        "   gridline-color: #D2B48C;"
        "   font-size: 12px;"
        "   border: 1px solid #BC8F8F;"
        "   border-top: none;"
        "   border-radius: 0 0 8px 8px;"
        "   selection-background-color: #DEB887;"
        "}"
        ""
        "#pciTable::item {"
        "   padding: 8px;"
        "   border-bottom: 1px solid #F5DEB3;"
        "}"
        ""
        "#pciTable::item:alternate {"
        "   background-color: rgba(245, 222, 179, 100);"
        "}"
        ""
        "#pciTable::item:selected {"
        "   background-color: #DEB887;"
        "   color: #8B4513;"
        "}"
        ""
        "QHeaderView::section {"
        "   background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F5DEB3, stop:1 #D2B48C);"
        "   color: #8B4513;"
        "   padding: 12px;"
        "   border: 1px solid #BC8F8F;"
        "   font-weight: bold;"
        "   font-size: 13px;"
        "}"
        ""
        "#statusLabel {"
        "   color: #696969;"
        "   font-size: 12px;"
        "   background: rgba(255, 248, 220, 180);"
        "   padding: 8px 15px;"
        "   border-radius: 5px;"
        "   border: 1px solid #D2B48C;"
        "}"
    );
}

void PCIWindow::paintEvent(QPaintEvent *event)
{
    QPainter painter(this);
    QLinearGradient gradient(0, 0, width(), height());
    gradient.setColorAt(0, Colors::LightBeige);
    gradient.setColorAt(1, Colors::DarkBeige);
    painter.fillRect(rect(), gradient);

    painter.setPen(QPen(QColor(220, 200, 160, 80), 2));
    for (int i = 0; i < width(); i += 20) {
        painter.drawLine(i, 0, i, height());
    }
    for (int i = 0; i < height(); i += 20) {
        painter.drawLine(0, i, width(), i);
    }

    QWidget::paintEvent(event);
}

void PCIWindow::onScanPCI()
{
    qDebug() << "Starting PCI scan...";

    if (!m_table) return;

    m_table->setRowCount(0);
    m_statusLabel->setText("Scanning PCI devices...");

    int devicesFound = 0;
    const int totalScans = 256 * 32 * 8;

    for (int bus = 0; bus < 256; ++bus) {
        for (int device = 0; device < 32; ++device) {
            for (int function = 0; function < 8; ++function) {
                if (checkDeviceExists(bus, device, function)) {
                    PCIDeviceInfo deviceInfo = scanDevice(bus, device, function);
                    if (validateDevice(deviceInfo)) {
                        addDeviceToTable(deviceInfo);
                        devicesFound++;
                    }
                }
            }
        }
    }

    m_statusLabel->setText(QString("Scan completed. Found %1 devices").arg(devicesFound));
    qDebug() << "PCI Scan: Found" << devicesFound << "devices out of" << totalScans << "possible addresses";

    m_table->resizeColumnsToContents();
    m_table->setColumnWidth(0, 120);
    m_table->setColumnWidth(1, 120);
}

PCIDeviceInfo PCIWindow::scanDevice(int bus, int device, int function)
{
    PCIDeviceInfo info;
    info.bus = bus;
    info.device = device;
    info.function = function;

    parseDeviceDetails(info);
    return info;
}

bool PCIWindow::validateDevice(const PCIDeviceInfo& deviceInfo)
{
    return deviceInfo.vendorID != 0xFFFF && deviceInfo.vendorID != 0;
}

QTableWidgetItem* PCIWindow::createTableItem(const QString& text, Qt::Alignment alignment)
{
    QTableWidgetItem *item = new QTableWidgetItem(text);
    item->setTextAlignment(alignment);
    return item;
}

void PCIWindow::addDeviceToTable(const PCIDeviceInfo& deviceInfo)
{
    if (!m_table) return;

    int row = m_table->rowCount();
    m_table->insertRow(row);

    m_table->setItem(row, 0, createTableItem(
        QString("0x%1").arg(deviceInfo.vendorID, 4, 16, QChar('0')).toUpper()
    ));

    m_table->setItem(row, 1, createTableItem(
        QString("0x%1").arg(deviceInfo.deviceID, 4, 16, QChar('0')).toUpper()
    ));


    QString description = QString("%1\n%2\nClass: %3\n%4")
        .arg(deviceInfo.vendorName)
        .arg(deviceInfo.deviceName)
        .arg(deviceInfo.className)
        .arg(deviceInfo.devicePath);

    m_table->setItem(row, 2, createTableItem(description, Qt::AlignLeft | Qt::AlignVCenter));
}

void PCIWindow::parseDeviceDetails(PCIDeviceInfo& info)
{
    unsigned long vendorDevice = readPCIConfig(info.bus, info.device, info.function, 0x00);
    info.deviceID = vendorDevice >> 16;
    info.vendorID = vendorDevice & 0xFFFF;

    unsigned long classRevision = readPCIConfig(info.bus, info.device, info.function, 0x08);
    unsigned long classID = classRevision >> 8;
    info.revisionID = classRevision & 0xFF;
    info.baseClass = classID >> 16;

    unsigned long progInterface = classID & 0xFFFF;
    info.subClass = progInterface >> 8;
    info.progIf = progInterface & 0xFF;

    unsigned long subsystem = readPCIConfig(info.bus, info.device, info.function, 0x2C);
    info.subsysID = subsystem >> 16;
    info.subsysVendID = subsystem & 0xFFFF;

    resolveDeviceNames(info);
    info.devicePath = formatDevicePath(info);
}

QString PCIWindow::formatDevicePath(const PCIDeviceInfo& info)
{
    return QString("PCI\\VEN_%1&DEV_%2&SUBSYS_%3%4&REV_%5\\%6&%7&%8&%9")
        .arg(info.vendorID, 4, 16, QChar('0')).toUpper()
        .arg(info.deviceID, 4, 16, QChar('0')).toUpper()
        .arg(info.subsysVendID, 4, 16, QChar('0')).toUpper()
        .arg(info.subsysID, 4, 16, QChar('0')).toUpper()
        .arg(info.revisionID, 2, 16, QChar('0')).toUpper()
        .arg(info.bus, 2, 16, QChar('0')).toUpper()
        .arg(info.device, 2, 16, QChar('0')).toUpper()
        .arg(info.function, 1, 16, QChar('0')).toUpper()
        .arg(0, 2, 16, QChar('0')).toUpper();
}

void PCIWindow::resolveDeviceNames(PCIDeviceInfo& info)
{
    info.vendorName = "Unknown Vendor";
    info.deviceName = "Unknown Device";
    info.className = "Unknown Class";

    for (int i = 0; i < PCI_CLASSCODETABLE_LEN; i++) {
        if (PciClassCodeTable[i].BaseClass == info.baseClass &&
            PciClassCodeTable[i].SubClass == info.subClass &&
            PciClassCodeTable[i].ProgIf == info.progIf) {
            info.className = QString("%1 (%2 %3)")
                .arg(PciClassCodeTable[i].BaseDesc)
                .arg(PciClassCodeTable[i].SubDesc)
                .arg(PciClassCodeTable[i].ProgDesc);
            break;
        }
    }

    for (int i = 0; i < PCI_DEVTABLE_LEN; i++) {
        if (PciDevTable[i].VenId == info.vendorID && PciDevTable[i].DevId == info.deviceID) {
            info.deviceName = QString("%1, %2")
                .arg(PciDevTable[i].Chip)
                .arg(PciDevTable[i].ChipDesc);
            break;
        }
    }

    for (int i = 0; i < PCI_VENTABLE_LEN; i++) {
        if (PciVenTable[i].VenId == info.vendorID) {
            info.vendorName = QString(PciVenTable[i].VenFull);
            break;
        }
    }
}

unsigned long PCIWindow::readPCIConfig(int bus, int device, int function, int reg)
{
    unsigned long configAddress = calculatePCIAddress(bus, device, function, reg);
    unsigned long regData;

    __asm {
        mov eax, configAddress
        mov dx, 0CF8h
        out dx, eax
        mov dx, 0CFCh
        in eax, dx
        mov regData, eax
    }

    return regData;
}

unsigned long PCIWindow::calculatePCIAddress(int bus, int device, int function, int reg)
{
    return (1 << 31) | (bus << 16) | (device << 11) | (function << 8) | (reg & 0xFC);
}

bool PCIWindow::checkDeviceExists(int bus, int device, int function)
{
    unsigned long vendorDevice = readPCIConfig(bus, device, function, 0x00);
    return (vendorDevice != 0xFFFFFFFF) && ((vendorDevice & 0xFFFF) != 0xFFFF);
}
