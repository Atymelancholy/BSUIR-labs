#ifndef LAB1WINDOW_H
#define LAB1WINDOW_H

#include <QMainWindow>
#include <QShowEvent>
#include <QResizeEvent>

namespace Ui {
class Lab1Window;
}

class Battery;
class CharacterAnimation;
class QLabel;

class Lab1Window : public QMainWindow
{
    Q_OBJECT

public:
    explicit Lab1Window(QWidget *parent = nullptr);
    ~Lab1Window();

signals:
    void backToMain();

protected:
    void resizeEvent(QResizeEvent *event) override;
    void showEvent(QShowEvent *event) override;

private slots:
    void updateBatteryInfo();
    void onSleepClicked();
    void onHibernateClicked();
    void onBackClicked();

private:
    Ui::Lab1Window *ui;
    QLabel *backgroundLabel;
    QLabel *batteryInfoLabel;
    CharacterAnimation *m_characterAnimation;
    QLabel *m_staticImageLabel; // Добавляем объявление статичной картинки

    void setupUI();
    void updateAnimationPosition();
};

#endif // LAB1WINDOW_H
