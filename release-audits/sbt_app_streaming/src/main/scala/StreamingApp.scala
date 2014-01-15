package main.scala

import scala.collection.mutable.{ListBuffer, Queue}

import org.apache.spark.SparkConf
import org.apache.spark.rdd.RDD
import org.apache.spark.streaming.StreamingContext
import org.apache.spark.streaming._

object SparkStreamingExample {

  def main(args: Array[String]) {
    val conf = new SparkConf(true)
      .setMaster("local[2]")
      .setAppName("Streaming test")
    val ssc = new StreamingContext(conf, Seconds(1))
    val seen = ListBuffer[RDD[Int]]()

    val rdd1 = ssc.sparkContext.makeRDD(1 to 100, 10)
    val rdd2 = ssc.sparkContext.makeRDD(1 to 1000, 10)
    val rdd3 = ssc.sparkContext.makeRDD(1 to 10000, 10)

    val queue = Queue(rdd1, rdd2, rdd3)
    val stream = ssc.queueStream(queue)

    stream.foreachRDD(rdd => seen += rdd)
    ssc.start()
    Thread.sleep(5000)

    def test(f: => Boolean, failureMsg: String) = {
      if (!f) {
        println(failureMsg)
        System.exit(-1)
      }
    }

    val rddCounts = seen.map(rdd => rdd.count()).filter(_ > 0)
    test(rddCounts.length == 3, "Did not collect three RDD's from stream")
    test(rddCounts.toSet == Set(100, 1000, 10000), "Did not find expected streams")

    println("Test succeeded")

    ssc.stop()
  }
}
