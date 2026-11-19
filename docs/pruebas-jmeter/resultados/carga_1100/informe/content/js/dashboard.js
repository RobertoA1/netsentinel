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

    var data = {"OkPercent": 50.08822232024702, "KoPercent": 49.91177767975298};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.00755750273822563, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.026363636363636363, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.02409090909090909, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.01, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0022727272727272726, 500, 1500, "GET /health"], "isController": false}, {"data": [0.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 9068, 4526, 49.91177767975298, 8490.022606969573, 60, 30092, 5129.0, 28226.4, 30032.0, 30038.0, 96.26020402747258, 212.4444683290341, 23.447327513454983], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 1100, 618, 56.18181818181818, 4538.852727272724, 3976, 7699, 4213.0, 5207.8, 7350.95, 7630.98, 54.12320409368235, 10.595347557075378, 14.800274613757134], "isController": false}, {"data": ["GET /findings", 1100, 618, 56.18181818181818, 4615.825454545451, 3396, 5644, 4706.5, 5295.9, 5358.0, 5463.99, 60.18493188159982, 604.2235887317393, 17.221952453903814], "isController": false}, {"data": ["POST /auth/login", 1100, 618, 56.18181818181818, 22161.43818181819, 60, 30092, 30031.0, 30037.0, 30040.0, 30047.0, 21.84056388364936, 53.4815378983421, 2.2803844435619975], "isController": false}, {"data": ["GET /auth/me", 1100, 733, 66.63636363636364, 8414.273636363636, 2024, 30050, 3610.5, 30030.0, 30032.0, 30036.99, 19.604348600962396, 18.722988326501515, 4.170014118472643], "isController": false}, {"data": ["GET /dashboard/summary", 1100, 619, 56.27272727272727, 5245.936363636364, 780, 30030, 4903.5, 7088.0, 11025.450000000003, 20643.57, 25.1520556089084, 9.481815849796497, 6.550051697477935], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1100, 618, 56.18181818181818, 6174.00909090909, 1071, 7686, 6361.5, 7492.0, 7585.95, 7640.99, 56.87693898655636, 11.134428322130299, 15.442210121509824], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 1100, 618, 56.18181818181818, 3741.913636363638, 3317, 5779, 3655.5, 4164.6, 4319.75, 5008.780000000001, 61.452513966480446, 16.132376047486034, 16.804512918994416], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 62, 61, 98.38709677419355, 74972.01612903227, 70355, 80762, 74608.5, 79773.5, 80381.15, 80762.0, 0.7558763288793524, 37.29860601013118, 2.157035878980542], "isController": true}, {"data": ["GET /alerts/unread-count", 26, 0, 0.0, 5426.461538461539, 5251, 5549, 5441.0, 5499.7, 5536.4, 5549.0, 3.6910846110164677, 0.6488234667802385, 1.394970453577513], "isController": false}, {"data": ["GET /health", 1100, 11, 1.0, 13880.245454545471, 994, 30033, 10627.0, 28480.2, 28900.9, 30028.93, 20.14910336490026, 4.8660871700584325, 4.964042150550436], "isController": false}, {"data": ["GET /logs", 242, 73, 30.165289256198346, 4945.012396694215, 3542, 5671, 5303.0, 5579.7, 5621.85, 5663.0, 19.65721712289822, 310.37410649013077, 6.308985612460401], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["401/Unauthorized", 3781, 83.53954927087936, 41.69607410674901], "isController": false}, {"data": ["Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 745, 16.460450729120637, 8.21570357300397], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 9068, 4526, "401/Unauthorized", 3781, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 745, "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": ["GET /dashboard/top-talkers", 1100, 618, "401/Unauthorized", 618, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /findings", 1100, 618, "401/Unauthorized", 618, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["POST /auth/login", 1100, 618, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 618, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /auth/me", 1100, 733, "401/Unauthorized", 618, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 115, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/summary", 1100, 619, "401/Unauthorized", 618, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 1, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1100, 618, "401/Unauthorized", 618, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 1100, 618, "401/Unauthorized", 618, "", "", "", "", "", "", "", ""], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": ["GET /health", 1100, 11, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 11, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /logs", 242, 73, "401/Unauthorized", 73, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
