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
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 85.62753036437248, "KoPercent": 14.37246963562753};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.05902162353775257, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.034166666666666665, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.13166666666666665, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.008333333333333333, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.3795681063122924, 500, 1500, "GET /health"], "isController": false}, {"data": [0.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 5434, 781, 14.37246963562753, 8937.176297386826, 105, 30034, 4321.5, 30030.0, 30030.0, 30031.0, 45.57080918796072, 129.621291317939, 14.139227512306803], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 600, 0, 0.0, 3990.1150000000016, 3376, 5122, 3798.0, 4842.9, 4977.799999999999, 5065.97, 27.92776019363247, 4.609171360081921, 10.854734919009495], "isController": false}, {"data": ["GET /findings", 600, 237, 39.5, 14271.123333333333, 3464, 30031, 4227.5, 30030.0, 30030.95, 30031.0, 12.690355329949238, 187.21626397921955, 3.081562797430203], "isController": false}, {"data": ["POST /auth/login", 600, 0, 0.0, 12970.066666666677, 105, 20210, 16546.5, 19626.1, 19859.85, 20012.96, 22.177046756606913, 47.51605525780817, 5.284374422472741], "isController": false}, {"data": ["GET /auth/me", 600, 0, 0.0, 4347.236666666672, 354, 22983, 3374.0, 9677.099999999997, 17127.54999999999, 21751.36, 18.08154778049001, 29.84161694241027, 6.621660564144291], "isController": false}, {"data": ["GET /dashboard/summary", 600, 0, 0.0, 4025.1283333333326, 493, 5163, 4424.0, 4988.9, 5052.95, 5132.97, 37.83102143757881, 21.72328184110971, 14.223577395964691], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 600, 0, 0.0, 4500.763333333334, 2225, 5096, 4450.5, 4995.8, 5030.0, 5078.93, 30.58883507519755, 5.048352663777721, 11.829276064236554], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 600, 0, 0.0, 3676.3699999999963, 3400, 4956, 3678.5, 3824.9, 3866.95, 4126.320000000001, 26.997840172786177, 8.568650445464362, 10.493301160907127], "isController": false}, {"data": ["GET /alerts/unread-count", 153, 152, 99.34640522875817, 29861.320261437908, 4420, 30034, 30030.0, 30031.0, 30031.0, 30032.38, 2.414467870218407, 6.449245380160333, 0.005964046324643353], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 208, 207, 99.51923076923077, 77716.55288461538, 47682, 102912, 72785.5, 98002.7, 99320.59999999999, 102714.98, 1.9491533365194493, 75.7339030126367, 5.532609590092116], "isController": true}, {"data": ["GET /health", 602, 2, 0.33222591362126247, 5355.365448504976, 274, 30030, 1147.5, 13058.1, 13652.800000000001, 14466.16, 5.124276472591079, 1.1529888066053795, 1.8653441011235954], "isController": false}, {"data": ["GET /logs", 479, 390, 81.419624217119, 25268.104384133614, 3666, 30032, 30030.0, 30031.0, 30031.0, 30031.0, 6.950692167048785, 44.28604798643962, 0.4943888397132658], "isController": false}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 781, 100.0, 14.37246963562753], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 5434, 781, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 781, "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": ["GET /findings", 600, 237, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 237, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": ["GET /alerts/unread-count", 153, 152, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 152, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": ["GET /health", 602, 2, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 2, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /logs", 479, 390, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 390, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
