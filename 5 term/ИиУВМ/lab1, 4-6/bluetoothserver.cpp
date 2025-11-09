#include "bluetoothserver.h"
#include <QBluetoothLocalDevice>
#include <QBluetoothUuid>
#include <QDebug>
#include <QDir>
#include <QFileInfo>
#include <QStandardPaths>

#ifdef Q_OS_WIN
#include <windows.h>
#include <shellapi.h>
#endif

BluetoothServer::BluetoothServer(QObject *parent)
    : QObject(parent)
    , m_server(nullptr)
    , m_clientSocket(nullptr)
    , m_currentFile(nullptr)
    , m_expectedFileSize(0)
    , m_receivedBytes(0)
    , m_playbackProcess(nullptr)
    , m_receivingFile(false)
{
}

BluetoothServer::~BluetoothServer()
{
    stopServer();
    if (m_playbackProcess) {
        m_playbackProcess->terminate();
        m_playbackProcess->waitForFinished(3000);
        delete m_playbackProcess;
    }
}

bool BluetoothServer::startServer()
{
    if (m_server) {
        emit statusMessage("Сервер уже запущен");
        return true;
    }

    m_server = new QBluetoothServer(QBluetoothServiceInfo::RfcommProtocol, this);

    connect(m_server, &QBluetoothServer::newConnection,
            this, &BluetoothServer::onClientConnected);

    QBluetoothAddress localAdapter = QBluetoothAddress();
    bool result = m_server->listen(localAdapter);

    if (!result) {
        emit statusMessage("Ошибка запуска сервера: " + m_server->errorString());
        delete m_server;
        m_server = nullptr;
        return false;
    }

    // Регистрируем сервис
    QBluetoothServiceInfo serviceInfo;
    serviceInfo.setAttribute(QBluetoothServiceInfo::ServiceName, tr("File Transfer Service"));

    QBluetoothServiceInfo::Sequence classId;
    classId << QVariant::fromValue(QBluetoothUuid(QBluetoothUuid::ServiceClassUuid::SerialPort));
    serviceInfo.setAttribute(QBluetoothServiceInfo::ServiceClassIds, classId);

    serviceInfo.setServiceUuid(QBluetoothUuid(QString("00001101-0000-1000-8000-00805f9b34fb")));

    QBluetoothServiceInfo::Sequence protocolDescriptorList;
    QBluetoothServiceInfo::Sequence protocol;
    protocol << QVariant::fromValue(QBluetoothUuid(QBluetoothUuid::ProtocolUuid::L2cap));
    protocolDescriptorList.append(QVariant::fromValue(protocol));
    protocol.clear();

    protocol << QVariant::fromValue(QBluetoothUuid(QBluetoothUuid::ProtocolUuid::Rfcomm))
             << QVariant::fromValue(quint8(m_server->serverPort()));
    protocolDescriptorList.append(QVariant::fromValue(protocol));

    serviceInfo.setAttribute(QBluetoothServiceInfo::ProtocolDescriptorList, protocolDescriptorList);
    serviceInfo.setServiceAvailability(0xFF);

    if (!serviceInfo.registerService(localAdapter)) {
        emit statusMessage("Ошибка регистрации сервиса");
        delete m_server;
        m_server = nullptr;
        return false;
    }

    emit statusMessage(QString("Сервер запущен на порту %1").arg(m_server->serverPort()));
    return true;
}

void BluetoothServer::stopServer()
{
    if (m_clientSocket) {
        m_clientSocket->close();
        delete m_clientSocket;
        m_clientSocket = nullptr;
    }

    if (m_server) {
        m_server->close();
        delete m_server;
        m_server = nullptr;
    }

    if (m_currentFile) {
        m_currentFile->close();
        delete m_currentFile;
        m_currentFile = nullptr;
    }

    emit statusMessage("Сервер остановлен");
}

bool BluetoothServer::isRunning() const
{
    return m_server && m_server->isListening();
}

void BluetoothServer::onClientConnected()
{
    m_clientSocket = m_server->nextPendingConnection();
    if (!m_clientSocket) {
        emit statusMessage("Ошибка: Неверное соединение с клиентом");
        return;
    }

    connect(m_clientSocket, &QBluetoothSocket::disconnected,
            this, &BluetoothServer::onClientDisconnected);
    connect(m_clientSocket, &QBluetoothSocket::readyRead,
            this, &BluetoothServer::onReadyRead);

    QString deviceName = m_clientSocket->peerName();
    if (deviceName.isEmpty()) {
        deviceName = m_clientSocket->peerAddress().toString();
    }

    emit clientConnected(deviceName);
    emit statusMessage("Клиент подключен: " + deviceName);
}

void BluetoothServer::onClientDisconnected()
{
    QString deviceName = "Unknown";
    if (m_clientSocket) {
        deviceName = m_clientSocket->peerName();
        if (deviceName.isEmpty()) {
            deviceName = m_clientSocket->peerAddress().toString();
        }
    }

    if (m_currentFile) {
        m_currentFile->close();
        delete m_currentFile;
        m_currentFile = nullptr;
    }

    m_receivingFile = false;
    m_receivedBytes = 0;
    m_expectedFileSize = 0;

    emit clientDisconnected(deviceName);
    emit statusMessage("Клиент отключен: " + deviceName);
}

void BluetoothServer::onReadyRead()
{
    if (!m_clientSocket) return;

    QByteArray data = m_clientSocket->readAll();

    if (!m_receivingFile) {
        // Обработка команд
        if (data.startsWith("FILE:")) {
            QString fileInfo = QString::fromUtf8(data).trimmed();
            QStringList parts = fileInfo.split(":");

            if (parts.size() >= 4) {
                m_currentFileName = parts[1];
                m_expectedFileSize = parts[2].toLongLong();
                QString fileExtension = parts[3];

                // Создаем папку для принятых файлов
                QDir dir("received_files");
                if (!dir.exists()) {
                    dir.mkpath(".");
                }

                QString filePath = dir.filePath(m_currentFileName);
                m_currentFile = new QFile(filePath);

                if (m_currentFile->open(QIODevice::WriteOnly)) {
                    m_receivingFile = true;
                    m_receivedBytes = 0;

                    emit statusMessage(QString("Начата загрузка файла: %1 (%2 байт)")
                                           .arg(m_currentFileName).arg(m_expectedFileSize));

                    // Отправляем подтверждение клиенту
                    m_clientSocket->write("READY");
                } else {
                    emit statusMessage("Ошибка создания файла: " + m_currentFile->errorString());
                    delete m_currentFile;
                    m_currentFile = nullptr;
                }
            }
        }
    } else {
        // Прием данных файла
        if (m_currentFile && m_currentFile->isOpen()) {
            qint64 bytesWritten = m_currentFile->write(data);
            m_receivedBytes += bytesWritten;

            if (m_receivedBytes >= m_expectedFileSize) {
                m_currentFile->close();

                emit fileReceived(m_currentFileName, m_receivedBytes);
                emit statusMessage(QString("Файл получен: %1 (%2 байт)")
                                       .arg(m_currentFileName).arg(m_receivedBytes));

                // Проверяем команду автовоспроизведения
                if (data.contains("AUTOPLAY")) {
                    startAutoPlayback(m_currentFile->fileName());
                }

                delete m_currentFile;
                m_currentFile = nullptr;
                m_receivingFile = false;
            }
        }
    }
}

void BluetoothServer::startAutoPlayback(const QString &filePath)
{
    emit statusMessage("Запуск автовоспроизведения: " + filePath);

    QString command = getMediaPlayerCommand(filePath);
    if (command.isEmpty()) {
        emit playbackError("Не найден подходящий медиаплеер");
        return;
    }

#ifdef Q_OS_WIN
    // На Windows используем ShellExecute для открытия файла ассоциированной программой
    LPCWSTR filePathW = reinterpret_cast<LPCWSTR>(filePath.utf16());
    HINSTANCE result = ShellExecuteW(NULL, L"open", filePathW, NULL, NULL, SW_SHOWNORMAL);

    if (reinterpret_cast<INT_PTR>(result) <= 32) {
        emit playbackError("Ошибка запуска воспроизведения");
    } else {
        emit playbackStarted(filePath);
        emit statusMessage("Воспроизведение запущено");
    }
#else
    m_playbackProcess = new QProcess(this);
    connect(m_playbackProcess, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished),
            this, &BluetoothServer::onPlaybackFinished);

    QStringList arguments;

#ifdef Q_OS_MACOS
    arguments << "-a" << "QuickTime Player" << filePath;
    m_playbackProcess->start("open", arguments);
#else
        // Linux - пробуем различные плееры
    QStringList players = {"vlc", "mplayer", "mpv", "ffplay", "xdg-open"};
    for (const QString &player : players) {
        m_playbackProcess->start("which", QStringList() << player);
        if (m_playbackProcess->waitForFinished(1000) && m_playbackProcess->exitCode() == 0) {
            if (player == "ffplay") {
                arguments << "-autoexit" << "-nodisp" << filePath;
            } else if (player == "xdg-open") {
                arguments.clear();
                arguments << filePath;
            } else {
                arguments.clear();
                arguments << filePath;
            }
            m_playbackProcess->start(player, arguments);
            break;
        }
    }
#endif

    if (m_playbackProcess->state() == QProcess::Running) {
        emit playbackStarted(filePath);
        emit statusMessage("Воспроизведение запущено");
    } else {
        emit playbackError("Не удалось запустить медиаплеер");
    }
#endif
}

QString BluetoothServer::getMediaPlayerCommand(const QString &filePath)
{
    Q_UNUSED(filePath)

// Для Windows команда не нужна - используем ShellExecute
#ifdef Q_OS_WIN
    return "system";
#elif defined(Q_OS_MACOS)
    return "open";
#else
    return "xdg-open"; // Linux
#endif
}

void BluetoothServer::onPlaybackFinished(int exitCode, QProcess::ExitStatus exitStatus)
{
    Q_UNUSED(exitCode)
    Q_UNUSED(exitStatus)

    if (m_playbackProcess) {
        m_playbackProcess->deleteLater();
        m_playbackProcess = nullptr;
    }

    emit statusMessage("Воспроизведение завершено");
}
