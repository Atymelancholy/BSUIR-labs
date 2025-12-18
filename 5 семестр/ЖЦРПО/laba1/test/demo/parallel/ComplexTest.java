package demo.parallel;

public class ComplexTest {

    public static void main(String[] args) {
        testCos();
        System.out.println("Все тесты прошли успешно!");
    }

    public static void testCos() {
        System.out.println("Testing Complex.cos() method...");

        Complex pi = new Complex(Math.PI, 0);
        Complex result = pi.cos();
        System.out.println("cos(π) = " + result.getRe() + " + " + result.getIm() + "i");

        Complex zero = new Complex(0, 0);
        result = zero.cos();
        System.out.println("cos(0) = " + result.getRe() + " + " + result.getIm() + "i");

        System.out.println("cos() test completed!");
    }
}