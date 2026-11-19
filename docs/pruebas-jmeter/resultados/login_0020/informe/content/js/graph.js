/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
$(document).ready(function() {

    $(".click-title").mouseenter( function(    e){
        e.preventDefault();
        this.style.cursor="pointer";
    });
    $(".click-title").mousedown( function(event){
        event.preventDefault();
    });

    // Ugly code while this script is shared among several pages
    try{
        refreshHitsPerSecond(true);
    } catch(e){}
    try{
        refreshResponseTimeOverTime(true);
    } catch(e){}
    try{
        refreshResponseTimePercentiles();
    } catch(e){}
});


var responseTimePercentilesInfos = {
        data: {"result": {"minY": 69.0, "minX": 0.0, "maxY": 3029.0, "series": [{"data": [[0.0, 69.0], [0.1, 71.0], [0.2, 73.0], [0.3, 74.0], [0.4, 77.0], [0.5, 79.0], [0.6, 86.0], [0.7, 87.0], [0.8, 92.0], [0.9, 93.0], [1.0, 93.0], [1.1, 93.0], [1.2, 97.0], [1.3, 100.0], [1.4, 104.0], [1.5, 110.0], [1.6, 113.0], [1.7, 115.0], [1.8, 119.0], [1.9, 124.0], [2.0, 126.0], [2.1, 128.0], [2.2, 137.0], [2.3, 140.0], [2.4, 145.0], [2.5, 171.0], [2.6, 175.0], [2.7, 218.0], [2.8, 219.0], [2.9, 220.0], [3.0, 229.0], [3.1, 230.0], [3.2, 255.0], [3.3, 260.0], [3.4, 269.0], [3.5, 270.0], [3.6, 287.0], [3.7, 293.0], [3.8, 303.0], [3.9, 304.0], [4.0, 307.0], [4.1, 310.0], [4.2, 322.0], [4.3, 323.0], [4.4, 327.0], [4.5, 339.0], [4.6, 342.0], [4.7, 344.0], [4.8, 344.0], [4.9, 346.0], [5.0, 349.0], [5.1, 358.0], [5.2, 364.0], [5.3, 374.0], [5.4, 375.0], [5.5, 377.0], [5.6, 403.0], [5.7, 410.0], [5.8, 415.0], [5.9, 416.0], [6.0, 419.0], [6.1, 419.0], [6.2, 423.0], [6.3, 424.0], [6.4, 427.0], [6.5, 427.0], [6.6, 430.0], [6.7, 431.0], [6.8, 439.0], [6.9, 459.0], [7.0, 460.0], [7.1, 464.0], [7.2, 465.0], [7.3, 467.0], [7.4, 469.0], [7.5, 473.0], [7.6, 473.0], [7.7, 475.0], [7.8, 475.0], [7.9, 485.0], [8.0, 494.0], [8.1, 500.0], [8.2, 510.0], [8.3, 533.0], [8.4, 534.0], [8.5, 536.0], [8.6, 540.0], [8.7, 543.0], [8.8, 550.0], [8.9, 552.0], [9.0, 565.0], [9.1, 567.0], [9.2, 568.0], [9.3, 581.0], [9.4, 581.0], [9.5, 582.0], [9.6, 586.0], [9.7, 587.0], [9.8, 589.0], [9.9, 591.0], [10.0, 593.0], [10.1, 596.0], [10.2, 600.0], [10.3, 601.0], [10.4, 605.0], [10.5, 617.0], [10.6, 617.0], [10.7, 618.0], [10.8, 620.0], [10.9, 622.0], [11.0, 626.0], [11.1, 631.0], [11.2, 637.0], [11.3, 639.0], [11.4, 640.0], [11.5, 640.0], [11.6, 645.0], [11.7, 645.0], [11.8, 647.0], [11.9, 648.0], [12.0, 653.0], [12.1, 653.0], [12.2, 657.0], [12.3, 661.0], [12.4, 663.0], [12.5, 664.0], [12.6, 664.0], [12.7, 668.0], [12.8, 669.0], [12.9, 670.0], [13.0, 671.0], [13.1, 676.0], [13.2, 679.0], [13.3, 682.0], [13.4, 682.0], [13.5, 684.0], [13.6, 686.0], [13.7, 686.0], [13.8, 686.0], [13.9, 688.0], [14.0, 689.0], [14.1, 690.0], [14.2, 695.0], [14.3, 695.0], [14.4, 696.0], [14.5, 697.0], [14.6, 700.0], [14.7, 701.0], [14.8, 701.0], [14.9, 702.0], [15.0, 704.0], [15.1, 705.0], [15.2, 705.0], [15.3, 710.0], [15.4, 710.0], [15.5, 710.0], [15.6, 712.0], [15.7, 714.0], [15.8, 716.0], [15.9, 718.0], [16.0, 722.0], [16.1, 722.0], [16.2, 724.0], [16.3, 725.0], [16.4, 726.0], [16.5, 729.0], [16.6, 730.0], [16.7, 731.0], [16.8, 732.0], [16.9, 732.0], [17.0, 735.0], [17.1, 737.0], [17.2, 737.0], [17.3, 738.0], [17.4, 740.0], [17.5, 740.0], [17.6, 742.0], [17.7, 743.0], [17.8, 746.0], [17.9, 746.0], [18.0, 747.0], [18.1, 748.0], [18.2, 748.0], [18.3, 750.0], [18.4, 751.0], [18.5, 751.0], [18.6, 752.0], [18.7, 753.0], [18.8, 753.0], [18.9, 754.0], [19.0, 756.0], [19.1, 757.0], [19.2, 758.0], [19.3, 758.0], [19.4, 761.0], [19.5, 763.0], [19.6, 765.0], [19.7, 765.0], [19.8, 768.0], [19.9, 768.0], [20.0, 769.0], [20.1, 769.0], [20.2, 769.0], [20.3, 770.0], [20.4, 770.0], [20.5, 771.0], [20.6, 772.0], [20.7, 773.0], [20.8, 774.0], [20.9, 775.0], [21.0, 776.0], [21.1, 776.0], [21.2, 776.0], [21.3, 777.0], [21.4, 778.0], [21.5, 778.0], [21.6, 778.0], [21.7, 780.0], [21.8, 780.0], [21.9, 781.0], [22.0, 781.0], [22.1, 782.0], [22.2, 782.0], [22.3, 784.0], [22.4, 784.0], [22.5, 784.0], [22.6, 785.0], [22.7, 785.0], [22.8, 786.0], [22.9, 787.0], [23.0, 787.0], [23.1, 788.0], [23.2, 789.0], [23.3, 789.0], [23.4, 790.0], [23.5, 791.0], [23.6, 791.0], [23.7, 792.0], [23.8, 792.0], [23.9, 793.0], [24.0, 794.0], [24.1, 794.0], [24.2, 794.0], [24.3, 794.0], [24.4, 795.0], [24.5, 796.0], [24.6, 796.0], [24.7, 797.0], [24.8, 797.0], [24.9, 797.0], [25.0, 798.0], [25.1, 799.0], [25.2, 800.0], [25.3, 802.0], [25.4, 803.0], [25.5, 804.0], [25.6, 804.0], [25.7, 804.0], [25.8, 805.0], [25.9, 806.0], [26.0, 807.0], [26.1, 807.0], [26.2, 807.0], [26.3, 808.0], [26.4, 808.0], [26.5, 809.0], [26.6, 810.0], [26.7, 810.0], [26.8, 810.0], [26.9, 812.0], [27.0, 812.0], [27.1, 812.0], [27.2, 813.0], [27.3, 813.0], [27.4, 815.0], [27.5, 815.0], [27.6, 815.0], [27.7, 815.0], [27.8, 816.0], [27.9, 816.0], [28.0, 818.0], [28.1, 818.0], [28.2, 818.0], [28.3, 819.0], [28.4, 820.0], [28.5, 821.0], [28.6, 821.0], [28.7, 821.0], [28.8, 822.0], [28.9, 822.0], [29.0, 823.0], [29.1, 823.0], [29.2, 823.0], [29.3, 825.0], [29.4, 825.0], [29.5, 826.0], [29.6, 826.0], [29.7, 827.0], [29.8, 827.0], [29.9, 828.0], [30.0, 829.0], [30.1, 829.0], [30.2, 829.0], [30.3, 830.0], [30.4, 830.0], [30.5, 831.0], [30.6, 831.0], [30.7, 832.0], [30.8, 832.0], [30.9, 832.0], [31.0, 833.0], [31.1, 834.0], [31.2, 834.0], [31.3, 834.0], [31.4, 835.0], [31.5, 835.0], [31.6, 835.0], [31.7, 835.0], [31.8, 836.0], [31.9, 837.0], [32.0, 837.0], [32.1, 838.0], [32.2, 838.0], [32.3, 838.0], [32.4, 839.0], [32.5, 839.0], [32.6, 840.0], [32.7, 840.0], [32.8, 841.0], [32.9, 842.0], [33.0, 842.0], [33.1, 842.0], [33.2, 843.0], [33.3, 843.0], [33.4, 843.0], [33.5, 843.0], [33.6, 843.0], [33.7, 844.0], [33.8, 844.0], [33.9, 844.0], [34.0, 844.0], [34.1, 844.0], [34.2, 844.0], [34.3, 845.0], [34.4, 845.0], [34.5, 845.0], [34.6, 846.0], [34.7, 847.0], [34.8, 847.0], [34.9, 848.0], [35.0, 848.0], [35.1, 849.0], [35.2, 849.0], [35.3, 849.0], [35.4, 849.0], [35.5, 850.0], [35.6, 850.0], [35.7, 850.0], [35.8, 850.0], [35.9, 851.0], [36.0, 851.0], [36.1, 851.0], [36.2, 851.0], [36.3, 852.0], [36.4, 852.0], [36.5, 852.0], [36.6, 853.0], [36.7, 853.0], [36.8, 853.0], [36.9, 854.0], [37.0, 854.0], [37.1, 855.0], [37.2, 855.0], [37.3, 855.0], [37.4, 857.0], [37.5, 857.0], [37.6, 857.0], [37.7, 858.0], [37.8, 858.0], [37.9, 858.0], [38.0, 859.0], [38.1, 859.0], [38.2, 860.0], [38.3, 861.0], [38.4, 861.0], [38.5, 861.0], [38.6, 861.0], [38.7, 861.0], [38.8, 861.0], [38.9, 862.0], [39.0, 863.0], [39.1, 863.0], [39.2, 863.0], [39.3, 864.0], [39.4, 864.0], [39.5, 865.0], [39.6, 866.0], [39.7, 866.0], [39.8, 866.0], [39.9, 867.0], [40.0, 867.0], [40.1, 868.0], [40.2, 868.0], [40.3, 869.0], [40.4, 869.0], [40.5, 869.0], [40.6, 869.0], [40.7, 870.0], [40.8, 870.0], [40.9, 871.0], [41.0, 871.0], [41.1, 872.0], [41.2, 872.0], [41.3, 873.0], [41.4, 873.0], [41.5, 874.0], [41.6, 874.0], [41.7, 874.0], [41.8, 875.0], [41.9, 875.0], [42.0, 875.0], [42.1, 875.0], [42.2, 876.0], [42.3, 876.0], [42.4, 876.0], [42.5, 876.0], [42.6, 877.0], [42.7, 879.0], [42.8, 879.0], [42.9, 880.0], [43.0, 880.0], [43.1, 880.0], [43.2, 881.0], [43.3, 881.0], [43.4, 882.0], [43.5, 882.0], [43.6, 884.0], [43.7, 884.0], [43.8, 885.0], [43.9, 885.0], [44.0, 885.0], [44.1, 886.0], [44.2, 886.0], [44.3, 886.0], [44.4, 886.0], [44.5, 886.0], [44.6, 886.0], [44.7, 887.0], [44.8, 888.0], [44.9, 888.0], [45.0, 888.0], [45.1, 888.0], [45.2, 889.0], [45.3, 889.0], [45.4, 889.0], [45.5, 890.0], [45.6, 891.0], [45.7, 891.0], [45.8, 891.0], [45.9, 892.0], [46.0, 892.0], [46.1, 892.0], [46.2, 892.0], [46.3, 894.0], [46.4, 894.0], [46.5, 894.0], [46.6, 894.0], [46.7, 895.0], [46.8, 895.0], [46.9, 895.0], [47.0, 895.0], [47.1, 895.0], [47.2, 895.0], [47.3, 896.0], [47.4, 896.0], [47.5, 897.0], [47.6, 897.0], [47.7, 897.0], [47.8, 898.0], [47.9, 898.0], [48.0, 898.0], [48.1, 898.0], [48.2, 898.0], [48.3, 898.0], [48.4, 898.0], [48.5, 899.0], [48.6, 899.0], [48.7, 900.0], [48.8, 900.0], [48.9, 900.0], [49.0, 901.0], [49.1, 901.0], [49.2, 901.0], [49.3, 901.0], [49.4, 902.0], [49.5, 902.0], [49.6, 903.0], [49.7, 903.0], [49.8, 903.0], [49.9, 903.0], [50.0, 904.0], [50.1, 904.0], [50.2, 904.0], [50.3, 904.0], [50.4, 904.0], [50.5, 905.0], [50.6, 905.0], [50.7, 905.0], [50.8, 906.0], [50.9, 906.0], [51.0, 907.0], [51.1, 907.0], [51.2, 907.0], [51.3, 908.0], [51.4, 908.0], [51.5, 910.0], [51.6, 910.0], [51.7, 910.0], [51.8, 910.0], [51.9, 910.0], [52.0, 911.0], [52.1, 912.0], [52.2, 912.0], [52.3, 912.0], [52.4, 912.0], [52.5, 913.0], [52.6, 913.0], [52.7, 913.0], [52.8, 913.0], [52.9, 913.0], [53.0, 914.0], [53.1, 914.0], [53.2, 914.0], [53.3, 915.0], [53.4, 915.0], [53.5, 915.0], [53.6, 915.0], [53.7, 916.0], [53.8, 916.0], [53.9, 916.0], [54.0, 916.0], [54.1, 916.0], [54.2, 917.0], [54.3, 917.0], [54.4, 918.0], [54.5, 918.0], [54.6, 918.0], [54.7, 918.0], [54.8, 919.0], [54.9, 919.0], [55.0, 919.0], [55.1, 920.0], [55.2, 920.0], [55.3, 921.0], [55.4, 921.0], [55.5, 921.0], [55.6, 922.0], [55.7, 923.0], [55.8, 923.0], [55.9, 924.0], [56.0, 924.0], [56.1, 924.0], [56.2, 924.0], [56.3, 924.0], [56.4, 925.0], [56.5, 925.0], [56.6, 925.0], [56.7, 925.0], [56.8, 926.0], [56.9, 926.0], [57.0, 927.0], [57.1, 928.0], [57.2, 928.0], [57.3, 928.0], [57.4, 929.0], [57.5, 929.0], [57.6, 930.0], [57.7, 930.0], [57.8, 931.0], [57.9, 931.0], [58.0, 931.0], [58.1, 931.0], [58.2, 931.0], [58.3, 932.0], [58.4, 933.0], [58.5, 933.0], [58.6, 934.0], [58.7, 934.0], [58.8, 934.0], [58.9, 934.0], [59.0, 935.0], [59.1, 935.0], [59.2, 935.0], [59.3, 935.0], [59.4, 935.0], [59.5, 936.0], [59.6, 936.0], [59.7, 936.0], [59.8, 937.0], [59.9, 937.0], [60.0, 937.0], [60.1, 938.0], [60.2, 938.0], [60.3, 938.0], [60.4, 938.0], [60.5, 939.0], [60.6, 939.0], [60.7, 939.0], [60.8, 940.0], [60.9, 940.0], [61.0, 940.0], [61.1, 941.0], [61.2, 941.0], [61.3, 941.0], [61.4, 941.0], [61.5, 942.0], [61.6, 942.0], [61.7, 943.0], [61.8, 943.0], [61.9, 943.0], [62.0, 944.0], [62.1, 944.0], [62.2, 945.0], [62.3, 945.0], [62.4, 946.0], [62.5, 946.0], [62.6, 946.0], [62.7, 947.0], [62.8, 947.0], [62.9, 947.0], [63.0, 948.0], [63.1, 948.0], [63.2, 948.0], [63.3, 948.0], [63.4, 949.0], [63.5, 949.0], [63.6, 951.0], [63.7, 951.0], [63.8, 952.0], [63.9, 953.0], [64.0, 953.0], [64.1, 954.0], [64.2, 955.0], [64.3, 955.0], [64.4, 955.0], [64.5, 955.0], [64.6, 957.0], [64.7, 957.0], [64.8, 957.0], [64.9, 957.0], [65.0, 958.0], [65.1, 959.0], [65.2, 959.0], [65.3, 959.0], [65.4, 960.0], [65.5, 960.0], [65.6, 960.0], [65.7, 961.0], [65.8, 961.0], [65.9, 962.0], [66.0, 962.0], [66.1, 962.0], [66.2, 962.0], [66.3, 963.0], [66.4, 963.0], [66.5, 964.0], [66.6, 964.0], [66.7, 966.0], [66.8, 966.0], [66.9, 966.0], [67.0, 966.0], [67.1, 967.0], [67.2, 967.0], [67.3, 967.0], [67.4, 968.0], [67.5, 968.0], [67.6, 968.0], [67.7, 968.0], [67.8, 968.0], [67.9, 968.0], [68.0, 969.0], [68.1, 969.0], [68.2, 969.0], [68.3, 970.0], [68.4, 970.0], [68.5, 971.0], [68.6, 971.0], [68.7, 972.0], [68.8, 972.0], [68.9, 972.0], [69.0, 972.0], [69.1, 972.0], [69.2, 972.0], [69.3, 973.0], [69.4, 973.0], [69.5, 973.0], [69.6, 973.0], [69.7, 973.0], [69.8, 974.0], [69.9, 976.0], [70.0, 976.0], [70.1, 977.0], [70.2, 977.0], [70.3, 977.0], [70.4, 978.0], [70.5, 978.0], [70.6, 978.0], [70.7, 979.0], [70.8, 979.0], [70.9, 979.0], [71.0, 980.0], [71.1, 980.0], [71.2, 981.0], [71.3, 981.0], [71.4, 982.0], [71.5, 983.0], [71.6, 983.0], [71.7, 985.0], [71.8, 985.0], [71.9, 985.0], [72.0, 986.0], [72.1, 988.0], [72.2, 988.0], [72.3, 989.0], [72.4, 989.0], [72.5, 989.0], [72.6, 990.0], [72.7, 990.0], [72.8, 990.0], [72.9, 990.0], [73.0, 993.0], [73.1, 993.0], [73.2, 994.0], [73.3, 994.0], [73.4, 995.0], [73.5, 995.0], [73.6, 997.0], [73.7, 997.0], [73.8, 998.0], [73.9, 998.0], [74.0, 999.0], [74.1, 1000.0], [74.2, 1000.0], [74.3, 1002.0], [74.4, 1003.0], [74.5, 1003.0], [74.6, 1003.0], [74.7, 1004.0], [74.8, 1004.0], [74.9, 1004.0], [75.0, 1005.0], [75.1, 1005.0], [75.2, 1006.0], [75.3, 1006.0], [75.4, 1007.0], [75.5, 1007.0], [75.6, 1008.0], [75.7, 1009.0], [75.8, 1009.0], [75.9, 1009.0], [76.0, 1010.0], [76.1, 1010.0], [76.2, 1011.0], [76.3, 1011.0], [76.4, 1012.0], [76.5, 1013.0], [76.6, 1014.0], [76.7, 1014.0], [76.8, 1015.0], [76.9, 1016.0], [77.0, 1017.0], [77.1, 1017.0], [77.2, 1018.0], [77.3, 1018.0], [77.4, 1018.0], [77.5, 1019.0], [77.6, 1020.0], [77.7, 1021.0], [77.8, 1022.0], [77.9, 1022.0], [78.0, 1024.0], [78.1, 1024.0], [78.2, 1024.0], [78.3, 1024.0], [78.4, 1026.0], [78.5, 1027.0], [78.6, 1027.0], [78.7, 1027.0], [78.8, 1028.0], [78.9, 1028.0], [79.0, 1028.0], [79.1, 1029.0], [79.2, 1031.0], [79.3, 1031.0], [79.4, 1032.0], [79.5, 1033.0], [79.6, 1033.0], [79.7, 1034.0], [79.8, 1034.0], [79.9, 1036.0], [80.0, 1036.0], [80.1, 1036.0], [80.2, 1037.0], [80.3, 1038.0], [80.4, 1040.0], [80.5, 1040.0], [80.6, 1042.0], [80.7, 1042.0], [80.8, 1042.0], [80.9, 1042.0], [81.0, 1043.0], [81.1, 1045.0], [81.2, 1045.0], [81.3, 1046.0], [81.4, 1048.0], [81.5, 1048.0], [81.6, 1049.0], [81.7, 1050.0], [81.8, 1050.0], [81.9, 1051.0], [82.0, 1051.0], [82.1, 1053.0], [82.2, 1054.0], [82.3, 1055.0], [82.4, 1057.0], [82.5, 1059.0], [82.6, 1060.0], [82.7, 1061.0], [82.8, 1061.0], [82.9, 1063.0], [83.0, 1063.0], [83.1, 1064.0], [83.2, 1064.0], [83.3, 1065.0], [83.4, 1065.0], [83.5, 1065.0], [83.6, 1065.0], [83.7, 1067.0], [83.8, 1068.0], [83.9, 1069.0], [84.0, 1071.0], [84.1, 1071.0], [84.2, 1072.0], [84.3, 1072.0], [84.4, 1073.0], [84.5, 1076.0], [84.6, 1076.0], [84.7, 1078.0], [84.8, 1079.0], [84.9, 1079.0], [85.0, 1080.0], [85.1, 1081.0], [85.2, 1083.0], [85.3, 1084.0], [85.4, 1085.0], [85.5, 1085.0], [85.6, 1089.0], [85.7, 1090.0], [85.8, 1091.0], [85.9, 1092.0], [86.0, 1094.0], [86.1, 1095.0], [86.2, 1097.0], [86.3, 1099.0], [86.4, 1099.0], [86.5, 1099.0], [86.6, 1100.0], [86.7, 1100.0], [86.8, 1104.0], [86.9, 1106.0], [87.0, 1107.0], [87.1, 1107.0], [87.2, 1109.0], [87.3, 1110.0], [87.4, 1111.0], [87.5, 1112.0], [87.6, 1115.0], [87.7, 1120.0], [87.8, 1120.0], [87.9, 1121.0], [88.0, 1122.0], [88.1, 1123.0], [88.2, 1124.0], [88.3, 1125.0], [88.4, 1125.0], [88.5, 1129.0], [88.6, 1130.0], [88.7, 1133.0], [88.8, 1135.0], [88.9, 1136.0], [89.0, 1141.0], [89.1, 1145.0], [89.2, 1148.0], [89.3, 1150.0], [89.4, 1154.0], [89.5, 1155.0], [89.6, 1159.0], [89.7, 1159.0], [89.8, 1161.0], [89.9, 1165.0], [90.0, 1176.0], [90.1, 1180.0], [90.2, 1181.0], [90.3, 1181.0], [90.4, 1182.0], [90.5, 1183.0], [90.6, 1198.0], [90.7, 1203.0], [90.8, 1210.0], [90.9, 1211.0], [91.0, 1216.0], [91.1, 1220.0], [91.2, 1224.0], [91.3, 1225.0], [91.4, 1228.0], [91.5, 1233.0], [91.6, 1235.0], [91.7, 1236.0], [91.8, 1240.0], [91.9, 1240.0], [92.0, 1245.0], [92.1, 1246.0], [92.2, 1270.0], [92.3, 1275.0], [92.4, 1283.0], [92.5, 1287.0], [92.6, 1288.0], [92.7, 1289.0], [92.8, 1290.0], [92.9, 1292.0], [93.0, 1298.0], [93.1, 1300.0], [93.2, 1300.0], [93.3, 1304.0], [93.4, 1323.0], [93.5, 1324.0], [93.6, 1325.0], [93.7, 1330.0], [93.8, 1338.0], [93.9, 1338.0], [94.0, 1340.0], [94.1, 1356.0], [94.2, 1358.0], [94.3, 1369.0], [94.4, 1374.0], [94.5, 1385.0], [94.6, 1391.0], [94.7, 1396.0], [94.8, 1407.0], [94.9, 1411.0], [95.0, 1413.0], [95.1, 1425.0], [95.2, 1442.0], [95.3, 1449.0], [95.4, 1450.0], [95.5, 1451.0], [95.6, 1459.0], [95.7, 1475.0], [95.8, 1479.0], [95.9, 1482.0], [96.0, 1488.0], [96.1, 1490.0], [96.2, 1504.0], [96.3, 1516.0], [96.4, 1518.0], [96.5, 1520.0], [96.6, 1544.0], [96.7, 1570.0], [96.8, 1571.0], [96.9, 1582.0], [97.0, 1604.0], [97.1, 1643.0], [97.2, 1653.0], [97.3, 1667.0], [97.4, 1672.0], [97.5, 1690.0], [97.6, 1759.0], [97.7, 1777.0], [97.8, 1812.0], [97.9, 1846.0], [98.0, 1934.0], [98.1, 1954.0], [98.2, 1984.0], [98.3, 2023.0], [98.4, 2066.0], [98.5, 2102.0], [98.6, 2210.0], [98.7, 2347.0], [98.8, 2392.0], [98.9, 2461.0], [99.0, 2513.0], [99.1, 2523.0], [99.2, 2606.0], [99.3, 2725.0], [99.4, 2762.0], [99.5, 2770.0], [99.6, 2810.0], [99.7, 2833.0], [99.8, 2905.0], [99.9, 2968.0]], "isOverall": false, "label": "POST /auth/login", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 100.0, "title": "Response Time Percentiles"}},
        getOptions: function() {
            return {
                series: {
                    points: { show: false }
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimePercentiles'
                },
                xaxis: {
                    tickDecimals: 1,
                    axisLabel: "Percentiles",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Percentile value in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : %x.2 percentile was %y ms"
                },
                selection: { mode: "xy" },
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimePercentiles"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimesPercentiles"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimesPercentiles"), dataset, prepareOverviewOptions(options));
        }
};

/**
 * @param elementId Id of element where we display message
 */
function setEmptyGraph(elementId) {
    $(function() {
        $(elementId).text("No graph series with filter="+seriesFilter);
    });
}

// Response times percentiles
function refreshResponseTimePercentiles() {
    var infos = responseTimePercentilesInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimePercentiles");
        return;
    }
    if (isGraph($("#flotResponseTimesPercentiles"))){
        infos.createGraph();
    } else {
        var choiceContainer = $("#choicesResponseTimePercentiles");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimesPercentiles", "#overviewResponseTimesPercentiles");
        $('#bodyResponseTimePercentiles .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var responseTimeDistributionInfos = {
        data: {"result": {"minY": 1.0, "minX": 0.0, "maxY": 322.0, "series": [{"data": [[0.0, 16.0], [600.0, 56.0], [700.0, 134.0], [800.0, 298.0], [900.0, 322.0], [1000.0, 158.0], [1100.0, 52.0], [1200.0, 31.0], [1300.0, 21.0], [1400.0, 18.0], [1500.0, 10.0], [100.0, 17.0], [1600.0, 8.0], [1700.0, 3.0], [1800.0, 2.0], [1900.0, 4.0], [2000.0, 2.0], [2100.0, 2.0], [2300.0, 2.0], [2200.0, 1.0], [2400.0, 2.0], [2500.0, 2.0], [2600.0, 2.0], [2800.0, 3.0], [2700.0, 3.0], [2900.0, 2.0], [3000.0, 1.0], [200.0, 14.0], [300.0, 24.0], [400.0, 31.0], [500.0, 27.0]], "isOverall": false, "label": "POST /auth/login", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 100, "maxX": 3000.0, "title": "Response Time Distribution"}},
        getOptions: function() {
            var granularity = this.data.result.granularity;
            return {
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimeDistribution'
                },
                xaxis:{
                    axisLabel: "Response times in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of responses",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                bars : {
                    show: true,
                    barWidth: this.data.result.granularity
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: function(label, xval, yval, flotItem){
                        return yval + " responses for " + label + " were between " + xval + " and " + (xval + granularity) + " ms";
                    }
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimeDistribution"), prepareData(data.result.series, $("#choicesResponseTimeDistribution")), options);
        }

};

// Response time distribution
function refreshResponseTimeDistribution() {
    var infos = responseTimeDistributionInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimeDistribution");
        return;
    }
    if (isGraph($("#flotResponseTimeDistribution"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimeDistribution");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        $('#footerResponseTimeDistribution .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var syntheticResponseTimeDistributionInfos = {
        data: {"result": {"minY": 49.0, "minX": 0.0, "ticks": [[0, "Requests having \nresponse time <= 500ms"], [1, "Requests having \nresponse time > 500ms and <= 1,500ms"], [2, "Requests having \nresponse time > 1,500ms"], [3, "Requests in error"]], "maxY": 1116.0, "series": [{"data": [[0.0, 103.0]], "color": "#9ACD32", "isOverall": false, "label": "Requests having \nresponse time <= 500ms", "isController": false}, {"data": [[1.0, 1116.0]], "color": "yellow", "isOverall": false, "label": "Requests having \nresponse time > 500ms and <= 1,500ms", "isController": false}, {"data": [[2.0, 49.0]], "color": "orange", "isOverall": false, "label": "Requests having \nresponse time > 1,500ms", "isController": false}, {"data": [], "color": "#FF6347", "isOverall": false, "label": "Requests in error", "isController": false}], "supportsControllersDiscrimination": false, "maxX": 2.0, "title": "Synthetic Response Times Distribution"}},
        getOptions: function() {
            return {
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendSyntheticResponseTimeDistribution'
                },
                xaxis:{
                    axisLabel: "Response times ranges",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                    tickLength:0,
                    min:-0.5,
                    max:3.5
                },
                yaxis: {
                    axisLabel: "Number of responses",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                bars : {
                    show: true,
                    align: "center",
                    barWidth: 0.25,
                    fill:.75
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: function(label, xval, yval, flotItem){
                        return yval + " " + label;
                    }
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var options = this.getOptions();
            prepareOptions(options, data);
            options.xaxis.ticks = data.result.ticks;
            $.plot($("#flotSyntheticResponseTimeDistribution"), prepareData(data.result.series, $("#choicesSyntheticResponseTimeDistribution")), options);
        }

};

// Response time distribution
function refreshSyntheticResponseTimeDistribution() {
    var infos = syntheticResponseTimeDistributionInfos;
    prepareSeries(infos.data, true);
    if (isGraph($("#flotSyntheticResponseTimeDistribution"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesSyntheticResponseTimeDistribution");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        $('#footerSyntheticResponseTimeDistribution .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var activeThreadsOverTimeInfos = {
        data: {"result": {"minY": 17.504694835680745, "minX": 1.7950296E12, "maxY": 19.775534441805227, "series": [{"data": [[1.7950296E12, 17.504694835680745], [1.79502966E12, 19.775534441805227]], "isOverall": false, "label": "Usuarios virtuales", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79502966E12, "title": "Active Threads Over Time"}},
        getOptions: function() {
            return {
                series: {
                    stack: true,
                    lines: {
                        show: true,
                        fill: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of active threads",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 6,
                    show: true,
                    container: '#legendActiveThreadsOverTime'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                selection: {
                    mode: 'xy'
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : At %x there were %y active threads"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesActiveThreadsOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotActiveThreadsOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewActiveThreadsOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Active Threads Over Time
function refreshActiveThreadsOverTime(fixTimestamps) {
    var infos = activeThreadsOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotActiveThreadsOverTime"))) {
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesActiveThreadsOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotActiveThreadsOverTime", "#overviewActiveThreadsOverTime");
        $('#footerActiveThreadsOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var timeVsThreadsInfos = {
        data: {"result": {"minY": 155.0, "minX": 1.0, "maxY": 966.0008718395816, "series": [{"data": [[2.0, 155.0], [8.0, 383.2], [9.0, 406.25], [10.0, 463.66666666666663], [11.0, 488.1428571428571], [3.0, 179.57142857142858], [12.0, 533.75], [13.0, 594.1428571428571], [14.0, 639.25], [15.0, 635.5], [1.0, 430.5], [4.0, 176.5], [16.0, 648.4285714285714], [17.0, 704.75], [18.0, 697.375], [19.0, 732.2], [5.0, 191.0], [20.0, 966.0008718395816], [6.0, 283.14285714285717], [7.0, 330.85714285714283]], "isOverall": false, "label": "POST /auth/login", "isController": false}, {"data": [[19.012618296529965, 914.6451104100931]], "isOverall": false, "label": "POST /auth/login-Aggregated", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 20.0, "title": "Time VS Threads"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    axisLabel: "Number of active threads",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response times in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: { noColumns: 2,show: true, container: '#legendTimeVsThreads' },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s: At %x.2 active threads, Average response time was %y.2 ms"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesTimeVsThreads"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotTimesVsThreads"), dataset, options);
            // setup overview
            $.plot($("#overviewTimesVsThreads"), dataset, prepareOverviewOptions(options));
        }
};

// Time vs threads
function refreshTimeVsThreads(){
    var infos = timeVsThreadsInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyTimeVsThreads");
        return;
    }
    if(isGraph($("#flotTimesVsThreads"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTimeVsThreads");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTimesVsThreads", "#overviewTimesVsThreads");
        $('#footerTimeVsThreads .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var bytesThroughputOverTimeInfos = {
        data : {"result": {"minY": 1732.4, "minX": 1.7950296E12, "maxY": 30789.133333333335, "series": [{"data": [[1.7950296E12, 15577.4], [1.79502966E12, 30789.133333333335]], "isOverall": false, "label": "Bytes received per second", "isController": false}, {"data": [[1.7950296E12, 1732.4], [1.79502966E12, 3424.133333333333]], "isOverall": false, "label": "Bytes sent per second", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79502966E12, "title": "Bytes Throughput Over Time"}},
        getOptions : function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity) ,
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Bytes / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendBytesThroughputOverTime'
                },
                selection: {
                    mode: "xy"
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y"
                }
            };
        },
        createGraph : function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesBytesThroughputOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotBytesThroughputOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewBytesThroughputOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Bytes throughput Over Time
function refreshBytesThroughputOverTime(fixTimestamps) {
    var infos = bytesThroughputOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotBytesThroughputOverTime"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesBytesThroughputOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotBytesThroughputOverTime", "#overviewBytesThroughputOverTime");
        $('#footerBytesThroughputOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var responseTimesOverTimeInfos = {
        data: {"result": {"minY": 820.7699530516428, "minX": 1.7950296E12, "maxY": 962.1401425178151, "series": [{"data": [[1.7950296E12, 820.7699530516428], [1.79502966E12, 962.1401425178151]], "isOverall": false, "label": "POST /auth/login", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79502966E12, "title": "Response Time Over Time"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average response time was %y ms"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Response Times Over Time
function refreshResponseTimeOverTime(fixTimestamps) {
    var infos = responseTimesOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimeOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotResponseTimesOverTime"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimesOverTime", "#overviewResponseTimesOverTime");
        $('#footerResponseTimesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var latenciesOverTimeInfos = {
        data: {"result": {"minY": 820.6619718309862, "minX": 1.7950296E12, "maxY": 962.1057007125895, "series": [{"data": [[1.7950296E12, 820.6619718309862], [1.79502966E12, 962.1057007125895]], "isOverall": false, "label": "POST /auth/login", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79502966E12, "title": "Latencies Over Time"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response latencies in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendLatenciesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average latency was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesLatenciesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotLatenciesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewLatenciesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Latencies Over Time
function refreshLatenciesOverTime(fixTimestamps) {
    var infos = latenciesOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyLatenciesOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotLatenciesOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesLatenciesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotLatenciesOverTime", "#overviewLatenciesOverTime");
        $('#footerLatenciesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var connectTimeOverTimeInfos = {
        data: {"result": {"minY": 0.0, "minX": 1.7950296E12, "maxY": 0.13849765258215982, "series": [{"data": [[1.7950296E12, 0.13849765258215982], [1.79502966E12, 0.0]], "isOverall": false, "label": "POST /auth/login", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79502966E12, "title": "Connect Time Over Time"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getConnectTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average Connect Time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendConnectTimeOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average connect time was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesConnectTimeOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotConnectTimeOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewConnectTimeOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Connect Time Over Time
function refreshConnectTimeOverTime(fixTimestamps) {
    var infos = connectTimeOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyConnectTimeOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotConnectTimeOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesConnectTimeOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotConnectTimeOverTime", "#overviewConnectTimeOverTime");
        $('#footerConnectTimeOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var responseTimePercentilesOverTimeInfos = {
        data: {"result": {"minY": 69.0, "minX": 1.7950296E12, "maxY": 3029.0, "series": [{"data": [[1.7950296E12, 2066.0], [1.79502966E12, 3029.0]], "isOverall": false, "label": "Max", "isController": false}, {"data": [[1.7950296E12, 69.0], [1.79502966E12, 263.0]], "isOverall": false, "label": "Min", "isController": false}, {"data": [[1.7950296E12, 1123.6], [1.79502966E12, 1200.1000000000001]], "isOverall": false, "label": "90th percentile", "isController": false}, {"data": [[1.7950296E12, 1948.6000000000004], [1.79502966E12, 2746.0899999999974]], "isOverall": false, "label": "99th percentile", "isController": false}, {"data": [[1.7950296E12, 876.0], [1.79502966E12, 915.0]], "isOverall": false, "label": "Median", "isController": false}, {"data": [[1.7950296E12, 1389.1499999999992], [1.79502966E12, 1472.5999999999985]], "isOverall": false, "label": "95th percentile", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79502966E12, "title": "Response Time Percentiles Over Time (successful requests only)"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true,
                        fill: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Response Time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimePercentilesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Response time was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimePercentilesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimePercentilesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimePercentilesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Response Time Percentiles Over Time
function refreshResponseTimePercentilesOverTime(fixTimestamps) {
    var infos = responseTimePercentilesOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotResponseTimePercentilesOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesResponseTimePercentilesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimePercentilesOverTime", "#overviewResponseTimePercentilesOverTime");
        $('#footerResponseTimePercentilesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var responseTimeVsRequestInfos = {
    data: {"result": {"minY": 78.0, "minX": 4.0, "maxY": 2392.0, "series": [{"data": [[14.0, 827.5], [15.0, 1147.0], [4.0, 78.0], [16.0, 1173.0], [17.0, 966.0], [18.0, 935.0], [19.0, 963.0], [20.0, 940.5], [5.0, 897.0], [21.0, 886.0], [22.0, 884.5], [23.0, 903.0], [24.0, 883.0], [25.0, 867.5], [26.0, 937.5], [27.0, 959.0], [30.0, 106.5], [31.0, 2392.0]], "isOverall": false, "label": "Successes", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 31.0, "title": "Response Time Vs Request"}},
    getOptions: function() {
        return {
            series: {
                lines: {
                    show: false
                },
                points: {
                    show: true
                }
            },
            xaxis: {
                axisLabel: "Global number of requests per second",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            yaxis: {
                axisLabel: "Median Response Time in ms",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            legend: {
                noColumns: 2,
                show: true,
                container: '#legendResponseTimeVsRequest'
            },
            selection: {
                mode: 'xy'
            },
            grid: {
                hoverable: true // IMPORTANT! this is needed for tooltip to work
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s : Median response time at %x req/s was %y ms"
            },
            colors: ["#9ACD32", "#FF6347"]
        };
    },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesResponseTimeVsRequest"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotResponseTimeVsRequest"), dataset, options);
        // setup overview
        $.plot($("#overviewResponseTimeVsRequest"), dataset, prepareOverviewOptions(options));

    }
};

// Response Time vs Request
function refreshResponseTimeVsRequest() {
    var infos = responseTimeVsRequestInfos;
    prepareSeries(infos.data);
    if (isGraph($("#flotResponseTimeVsRequest"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimeVsRequest");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimeVsRequest", "#overviewResponseTimeVsRequest");
        $('#footerResponseRimeVsRequest .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var latenciesVsRequestInfos = {
    data: {"result": {"minY": 78.0, "minX": 4.0, "maxY": 2392.0, "series": [{"data": [[14.0, 827.5], [15.0, 1147.0], [4.0, 78.0], [16.0, 1173.0], [17.0, 966.0], [18.0, 935.0], [19.0, 963.0], [20.0, 940.5], [5.0, 897.0], [21.0, 886.0], [22.0, 884.5], [23.0, 903.0], [24.0, 883.0], [25.0, 867.0], [26.0, 937.5], [27.0, 959.0], [30.0, 106.5], [31.0, 2392.0]], "isOverall": false, "label": "Successes", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 31.0, "title": "Latencies Vs Request"}},
    getOptions: function() {
        return{
            series: {
                lines: {
                    show: false
                },
                points: {
                    show: true
                }
            },
            xaxis: {
                axisLabel: "Global number of requests per second",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            yaxis: {
                axisLabel: "Median Latency in ms",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            legend: { noColumns: 2,show: true, container: '#legendLatencyVsRequest' },
            selection: {
                mode: 'xy'
            },
            grid: {
                hoverable: true // IMPORTANT! this is needed for tooltip to work
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s : Median Latency time at %x req/s was %y ms"
            },
            colors: ["#9ACD32", "#FF6347"]
        };
    },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesLatencyVsRequest"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotLatenciesVsRequest"), dataset, options);
        // setup overview
        $.plot($("#overviewLatenciesVsRequest"), dataset, prepareOverviewOptions(options));
    }
};

// Latencies vs Request
function refreshLatenciesVsRequest() {
        var infos = latenciesVsRequestInfos;
        prepareSeries(infos.data);
        if(isGraph($("#flotLatenciesVsRequest"))){
            infos.createGraph();
        }else{
            var choiceContainer = $("#choicesLatencyVsRequest");
            createLegend(choiceContainer, infos);
            infos.createGraph();
            setGraphZoomable("#flotLatenciesVsRequest", "#overviewLatenciesVsRequest");
            $('#footerLatenciesVsRequest .legendColorBox > div').each(function(i){
                $(this).clone().prependTo(choiceContainer.find("li").eq(i));
            });
        }
};

var hitsPerSecondInfos = {
        data: {"result": {"minY": 7.433333333333334, "minX": 1.7950296E12, "maxY": 13.7, "series": [{"data": [[1.7950296E12, 7.433333333333334], [1.79502966E12, 13.7]], "isOverall": false, "label": "hitsPerSecond", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79502966E12, "title": "Hits Per Second"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of hits / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendHitsPerSecond"
                },
                selection: {
                    mode : 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y.2 hits/sec"
                }
            };
        },
        createGraph: function createGraph() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesHitsPerSecond"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotHitsPerSecond"), dataset, options);
            // setup overview
            $.plot($("#overviewHitsPerSecond"), dataset, prepareOverviewOptions(options));
        }
};

// Hits per second
function refreshHitsPerSecond(fixTimestamps) {
    var infos = hitsPerSecondInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if (isGraph($("#flotHitsPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesHitsPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotHitsPerSecond", "#overviewHitsPerSecond");
        $('#footerHitsPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var codesPerSecondInfos = {
        data: {"result": {"minY": 7.1, "minX": 1.7950296E12, "maxY": 14.033333333333333, "series": [{"data": [[1.7950296E12, 7.1], [1.79502966E12, 14.033333333333333]], "isOverall": false, "label": "200", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79502966E12, "title": "Codes Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of responses / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendCodesPerSecond"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "Number of Response Codes %s at %x was %y.2 responses / sec"
                }
            };
        },
    createGraph: function() {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesCodesPerSecond"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotCodesPerSecond"), dataset, options);
        // setup overview
        $.plot($("#overviewCodesPerSecond"), dataset, prepareOverviewOptions(options));
    }
};

// Codes per second
function refreshCodesPerSecond(fixTimestamps) {
    var infos = codesPerSecondInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotCodesPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesCodesPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotCodesPerSecond", "#overviewCodesPerSecond");
        $('#footerCodesPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var transactionsPerSecondInfos = {
        data: {"result": {"minY": 7.1, "minX": 1.7950296E12, "maxY": 14.033333333333333, "series": [{"data": [[1.7950296E12, 7.1], [1.79502966E12, 14.033333333333333]], "isOverall": false, "label": "POST /auth/login-success", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79502966E12, "title": "Transactions Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of transactions / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendTransactionsPerSecond"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y transactions / sec"
                }
            };
        },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesTransactionsPerSecond"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotTransactionsPerSecond"), dataset, options);
        // setup overview
        $.plot($("#overviewTransactionsPerSecond"), dataset, prepareOverviewOptions(options));
    }
};

// Transactions per second
function refreshTransactionsPerSecond(fixTimestamps) {
    var infos = transactionsPerSecondInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyTransactionsPerSecond");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotTransactionsPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTransactionsPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTransactionsPerSecond", "#overviewTransactionsPerSecond");
        $('#footerTransactionsPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var totalTPSInfos = {
        data: {"result": {"minY": 7.1, "minX": 1.7950296E12, "maxY": 14.033333333333333, "series": [{"data": [[1.7950296E12, 7.1], [1.79502966E12, 14.033333333333333]], "isOverall": false, "label": "Transaction-success", "isController": false}, {"data": [], "isOverall": false, "label": "Transaction-failure", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79502966E12, "title": "Total Transactions Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of transactions / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendTotalTPS"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y transactions / sec"
                },
                colors: ["#9ACD32", "#FF6347"]
            };
        },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesTotalTPS"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotTotalTPS"), dataset, options);
        // setup overview
        $.plot($("#overviewTotalTPS"), dataset, prepareOverviewOptions(options));
    }
};

// Total Transactions per second
function refreshTotalTPS(fixTimestamps) {
    var infos = totalTPSInfos;
    // We want to ignore seriesFilter
    prepareSeries(infos.data, false, true);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotTotalTPS"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTotalTPS");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTotalTPS", "#overviewTotalTPS");
        $('#footerTotalTPS .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

// Collapse the graph matching the specified DOM element depending the collapsed
// status
function collapse(elem, collapsed){
    if(collapsed){
        $(elem).parent().find(".fa-chevron-up").removeClass("fa-chevron-up").addClass("fa-chevron-down");
    } else {
        $(elem).parent().find(".fa-chevron-down").removeClass("fa-chevron-down").addClass("fa-chevron-up");
        if (elem.id == "bodyBytesThroughputOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshBytesThroughputOverTime(true);
            }
            document.location.href="#bytesThroughputOverTime";
        } else if (elem.id == "bodyLatenciesOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshLatenciesOverTime(true);
            }
            document.location.href="#latenciesOverTime";
        } else if (elem.id == "bodyCustomGraph") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshCustomGraph(true);
            }
            document.location.href="#responseCustomGraph";
        } else if (elem.id == "bodyConnectTimeOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshConnectTimeOverTime(true);
            }
            document.location.href="#connectTimeOverTime";
        } else if (elem.id == "bodyResponseTimePercentilesOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimePercentilesOverTime(true);
            }
            document.location.href="#responseTimePercentilesOverTime";
        } else if (elem.id == "bodyResponseTimeDistribution") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimeDistribution();
            }
            document.location.href="#responseTimeDistribution" ;
        } else if (elem.id == "bodySyntheticResponseTimeDistribution") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshSyntheticResponseTimeDistribution();
            }
            document.location.href="#syntheticResponseTimeDistribution" ;
        } else if (elem.id == "bodyActiveThreadsOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshActiveThreadsOverTime(true);
            }
            document.location.href="#activeThreadsOverTime";
        } else if (elem.id == "bodyTimeVsThreads") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTimeVsThreads();
            }
            document.location.href="#timeVsThreads" ;
        } else if (elem.id == "bodyCodesPerSecond") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshCodesPerSecond(true);
            }
            document.location.href="#codesPerSecond";
        } else if (elem.id == "bodyTransactionsPerSecond") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTransactionsPerSecond(true);
            }
            document.location.href="#transactionsPerSecond";
        } else if (elem.id == "bodyTotalTPS") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTotalTPS(true);
            }
            document.location.href="#totalTPS";
        } else if (elem.id == "bodyResponseTimeVsRequest") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimeVsRequest();
            }
            document.location.href="#responseTimeVsRequest";
        } else if (elem.id == "bodyLatenciesVsRequest") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshLatenciesVsRequest();
            }
            document.location.href="#latencyVsRequest";
        }
    }
}

/*
 * Activates or deactivates all series of the specified graph (represented by id parameter)
 * depending on checked argument.
 */
function toggleAll(id, checked){
    var placeholder = document.getElementById(id);

    var cases = $(placeholder).find(':checkbox');
    cases.prop('checked', checked);
    $(cases).parent().children().children().toggleClass("legend-disabled", !checked);

    var choiceContainer;
    if ( id == "choicesBytesThroughputOverTime"){
        choiceContainer = $("#choicesBytesThroughputOverTime");
        refreshBytesThroughputOverTime(false);
    } else if(id == "choicesResponseTimesOverTime"){
        choiceContainer = $("#choicesResponseTimesOverTime");
        refreshResponseTimeOverTime(false);
    }else if(id == "choicesResponseCustomGraph"){
        choiceContainer = $("#choicesResponseCustomGraph");
        refreshCustomGraph(false);
    } else if ( id == "choicesLatenciesOverTime"){
        choiceContainer = $("#choicesLatenciesOverTime");
        refreshLatenciesOverTime(false);
    } else if ( id == "choicesConnectTimeOverTime"){
        choiceContainer = $("#choicesConnectTimeOverTime");
        refreshConnectTimeOverTime(false);
    } else if ( id == "choicesResponseTimePercentilesOverTime"){
        choiceContainer = $("#choicesResponseTimePercentilesOverTime");
        refreshResponseTimePercentilesOverTime(false);
    } else if ( id == "choicesResponseTimePercentiles"){
        choiceContainer = $("#choicesResponseTimePercentiles");
        refreshResponseTimePercentiles();
    } else if(id == "choicesActiveThreadsOverTime"){
        choiceContainer = $("#choicesActiveThreadsOverTime");
        refreshActiveThreadsOverTime(false);
    } else if ( id == "choicesTimeVsThreads"){
        choiceContainer = $("#choicesTimeVsThreads");
        refreshTimeVsThreads();
    } else if ( id == "choicesSyntheticResponseTimeDistribution"){
        choiceContainer = $("#choicesSyntheticResponseTimeDistribution");
        refreshSyntheticResponseTimeDistribution();
    } else if ( id == "choicesResponseTimeDistribution"){
        choiceContainer = $("#choicesResponseTimeDistribution");
        refreshResponseTimeDistribution();
    } else if ( id == "choicesHitsPerSecond"){
        choiceContainer = $("#choicesHitsPerSecond");
        refreshHitsPerSecond(false);
    } else if(id == "choicesCodesPerSecond"){
        choiceContainer = $("#choicesCodesPerSecond");
        refreshCodesPerSecond(false);
    } else if ( id == "choicesTransactionsPerSecond"){
        choiceContainer = $("#choicesTransactionsPerSecond");
        refreshTransactionsPerSecond(false);
    } else if ( id == "choicesTotalTPS"){
        choiceContainer = $("#choicesTotalTPS");
        refreshTotalTPS(false);
    } else if ( id == "choicesResponseTimeVsRequest"){
        choiceContainer = $("#choicesResponseTimeVsRequest");
        refreshResponseTimeVsRequest();
    } else if ( id == "choicesLatencyVsRequest"){
        choiceContainer = $("#choicesLatencyVsRequest");
        refreshLatenciesVsRequest();
    }
    var color = checked ? "black" : "#818181";
    if(choiceContainer != null) {
        choiceContainer.find("label").each(function(){
            this.style.color = color;
        });
    }
}

