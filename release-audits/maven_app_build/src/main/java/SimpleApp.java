/*** SimpleApp.java ***/
import org.apache.spark.api.java.*;
import org.apache.spark.api.java.function.Function;

public class SimpleApp {
  public static void main(String[] args) {
    String logFile = "input.txt";
    JavaSparkContext sc = new JavaSparkContext("local", "Simple App");
    JavaRDD<String> logData = sc.textFile(logFile).cache();

    long numAs = logData.filter(new Function<String, Boolean>() {
      public Boolean call(String s) { return s.contains("a"); }
    }).count();

    long numBs = logData.filter(new Function<String, Boolean>() {
      public Boolean call(String s) { return s.contains("b"); }
    }).count();

   if (numAs != 2 || numBs != 2) {
     System.out.println("Failed to parse log files with Spark");
     System.exit(-1);
   }
   System.out.println("Test succeeded");
  }
}
