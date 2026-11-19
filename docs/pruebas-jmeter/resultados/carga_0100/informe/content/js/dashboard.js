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

    var data = {"OkPercent": 100.0, "KoPercent": 0.0};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9964304370538046, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [1.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [1.0, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [1.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [1.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.9619666048237476, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [1.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 5204, 0, 0.0, 30.550153727901723, 2, 460, 17.0, 59.0, 90.75, 298.7999999999993, 58.84947245813025, 300.77135505603366, 22.26992974236393], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 565, 0, 0.0, 31.334513274336242, 7, 444, 16.0, 56.0, 103.99999999999932, 312.1000000000005, 6.957271272010836, 1.148221528290851, 2.7040956701760868], "isController": false}, {"data": ["GET /findings", 545, 0, 0.0, 36.15229357798169, 9, 407, 19.0, 59.400000000000034, 115.09999999999911, 367.0, 6.930403489362784, 156.8342188076209, 2.781636556765727], "isController": false}, {"data": ["POST /auth/login", 100, 0, 0.0, 79.31999999999995, 55, 154, 74.0, 110.9, 122.84999999999997, 153.90999999999997, 4.974876871797423, 10.659062360081588, 1.1854198796079798], "isController": false}, {"data": ["GET /auth/me", 598, 0, 0.0, 20.717391304347828, 4, 318, 12.0, 35.0, 56.09999999999991, 203.4499999999996, 7.014909615587646, 11.577341064788204, 2.5689366268021163], "isController": false}, {"data": ["GET /dashboard/summary", 588, 0, 0.0, 33.52040816326533, 10, 449, 21.0, 60.10000000000002, 82.54999999999995, 259.9900000000015, 6.995502890998644, 4.0169489256906274, 2.630145129916482], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 576, 0, 0.0, 30.90277777777776, 7, 414, 16.0, 53.30000000000007, 89.04999999999984, 332.84000000000015, 6.972437084649744, 1.150724479790827, 2.696372153829393], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 553, 0, 0.0, 31.0759493670886, 6, 385, 15.0, 57.0, 108.19999999999936, 325.9200000000001, 6.921324688978448, 2.1967094960136677, 2.690124244349045], "isController": false}, {"data": ["GET /alerts/unread-count", 526, 0, 0.0, 25.117870722433473, 6, 329, 14.0, 41.0, 69.64999999999998, 280.3800000000001, 6.915047458785791, 1.2155356861146898, 2.6134017251465833], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 539, 0, 0.0, 268.0742115027831, 107, 785, 225.0, 468.0, 545.0, 637.6000000000001, 6.962115243028197, 337.0007710679872, 23.84161440101913], "isController": true}, {"data": ["GET /health", 614, 0, 0.0, 11.416938110749191, 2, 241, 5.0, 18.5, 31.25, 168.55000000000007, 7.04864020939283, 1.5281231703957112, 2.5744057014774593], "isController": false}, {"data": ["GET /logs", 539, 0, 0.0, 48.86456400742113, 17, 460, 33.0, 79.0, 129.0, 378.6000000000007, 6.972923323716995, 156.99291721513214, 2.669322209860412], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": []}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 5204, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
