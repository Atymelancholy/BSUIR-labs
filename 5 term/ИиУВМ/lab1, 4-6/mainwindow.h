#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

namespace Ui {
class MainWindow;
}

class Lab1Window;
class Lab4Window;
class Lab5Window;
class Lab6Window;  // Добавляем предварительное объявление
class QLabel;
class QPushButton;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

protected:
    void resizeEvent(QResizeEvent *event) override;

private slots:
    void onPigButton1Clicked();
    void onPigButton2Clicked();
    void onPigButton3Clicked();
    void onPigButton4Clicked();
    void onPigButton5Clicked();
    void onPigButton6Clicked();
    void showLab1Window();
    void showLab2Window();
    void showLab3Window();
    void showLab4Window();
    void showLab5Window();
    void showLab6Window();  // Добавляем объявление
    void backToMain();

private:
    Ui::MainWindow *ui;
    void setupBackground();
    void setupUI();
    void positionElements();

    Lab1Window *m_lab1Window;
    Lab4Window *m_lab4Window;
    Lab5Window *m_lab5Window;
    Lab6Window *m_lab6Window;  // Добавляем указатель
    QLabel *characterImageLabel;
    QLabel *titleLabel;

    QLabel *pigImageLabels[6];
    QPushButton *pigButtons[6];
};

#endif // MAINWINDOW_H
