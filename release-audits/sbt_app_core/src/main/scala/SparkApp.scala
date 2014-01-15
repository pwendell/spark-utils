package main.scala

import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._

object SimpleApp {
  def main(args: Array[String]) {
    val logFile = "input.txt"
    val sc = new SparkContext("local", "Simple App")
    val logData = sc.textFile(logFile, 2).cache()
    val numAs = logData.filter(line => line.contains("a")).count()
    val numBs = logData.filter(line => line.contains("b")).count()
    if (numAs != 2 || numBs != 2) {
      println("Failed to parse log files with Spark")
      System.exit(-1)
    }
    println("Test succeeded")
  }
}

// vim: set ts=4 sw=4 et:
