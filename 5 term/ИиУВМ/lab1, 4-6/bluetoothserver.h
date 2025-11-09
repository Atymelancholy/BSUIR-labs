#ifndef BLUETOOTHSERVER_H
#define BLUETOOTHSERVER_H

#include <QObject>
#include <QBluetoothServer>
#include <QBluetoothSocket>
#include <QBluetoothServiceInfo>
#include <QFile>
#include <QProcess>

class BluetoothServer : public QObject
{
    Q_OBJECT

public:
    explicit BluetoothServer(QObject *parent = nullptr);
    ~BluetoothServer();

    bool startServer();
    void stopServer();
    bool isRunning() const;

signals:
    void clientConnected(const QString &deviceName);
    void clientDisconnected(const QString &deviceName);
    void fileReceived(const QString &fileName, qint64 fileSize);
    void playbackStarted(const QString &fileName);
    void playbackError(const QString &error);
    void statusMessage(const QString &message);

private slots:
    void onClientConnected();
    void onClientDisconnected();
    void onReadyRead();
    void onPlaybackFinished(int exitCode, QProcess::ExitStatus exitStatus);

private:
    void processFileData(const QByteArray &data);
    void startAutoPlayback(const QString &filePath);
    QString getMediaPlayerCommand(const QString &filePath);

    QBluetoothServer *m_server;
    QBluetoothSocket *m_clientSocket;
    QFile *m_currentFile;
    QString m_currentFileName;
    qint64 m_expectedFileSize;
    qint64 m_receivedBytes;
    QProcess *m_playbackProcess;
    bool m_receivingFile;
};

#endif // BLUETOOTHSERVER_H
