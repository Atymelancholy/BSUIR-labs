#ifndef LAB5WINDOW_H
#define LAB5WINDOW_H

#include <QMainWindow>
#include <QListWidgetItem>

// Предварительное объявление классов для уменьшения зависимостей
class USBManager;
class CharacterAnimation;
class QWidget;
class QGroupBox;
class QListWidget;
class QLabel;
class QPushButton;
class QHBoxLayout;
class QResizeEvent;
class QShowEvent;

/**
 * @class Lab5Window
 * @brief Главное окно приложения для мониторинга USB устройств
 *
 * Окно предоставляет интерфейс для просмотра подключенных USB устройств,
 * получения информации о них и безопасного извлечения.
 */
class Lab5Window : public QMainWindow
{
    Q_OBJECT

public:
    /**
     * @brief Конструктор главного окна
     * @param parent Родительский виджет
     */
    explicit Lab5Window(QWidget *parent = nullptr);

    /**
     * @brief Деструктор
     */
    ~Lab5Window();

protected:
    /**
     * @brief Обработчик изменения размера окна
     */
    void resizeEvent(QResizeEvent *event) override;

    /**
     * @brief Обработчик события показа окна
     */
    void showEvent(QShowEvent *event) override;

private slots:
    // Слоты для управления USB устройствами
    void refreshDeviceList();
    void handleDeviceEjection();
    void showDeviceDetails(QListWidgetItem* item);
    void returnToMainMenu();

    // Слоты для обработки сигналов от USBManager
    void updateDeviceDisplay();
    void onDeviceConnected(const QString& deviceName);
    void onDeviceDisconnected(const QString& deviceName);
    void onEjectionComplete(const QString& message);

private:
    // Методы инициализации интерфейса
    void initializeInterface();
    void setupDevicesPanel(QHBoxLayout *parentLayout);
    void setupInfoPanel(QHBoxLayout *parentLayout);
    void setupSignalHandlers();
    void applyCustomStyles();
    void centerOnScreen();

    // Методы работы с анимацией
    void initializeCharacterAnimation();
    void initializeAnimation();
    void updateAnimationPosition();
    void startConnectionAnimation();
    void startDisconnectionAnimation();

    // Вспомогательные методы
    void refreshDeviceListUI();

private:
    // Менеджер USB устройств
    USBManager *m_usbManager;

    // Анимационный компонент
    CharacterAnimation *m_characterAnimation;

    // Основные виджеты интерфейса
    QWidget *m_centralWidget;
    QGroupBox *m_devicesGroup;
    QGroupBox *m_infoGroup;
    QListWidget *m_devicesList;
    QLabel *m_deviceInfoLabel;
    QLabel *m_statusLabel;

    // Кнопки управления
    QPushButton *m_refreshButton;
    QPushButton *m_ejectButton;
    QPushButton *m_backButton;

    // Текущее выбранное устройство
    QString m_currentDeviceId;

signals:
    /**
     * @brief Сигнал для возврата в главное меню
     */
    void backToMain();
};

#endif // LAB5WINDOW_H
