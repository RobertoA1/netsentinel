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

    var data = {"OkPercent": 13.658686310620013, "KoPercent": 86.34131368937999};
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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.0017648864333947207, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0071875, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.0, 500, 1500, "GET /health"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 6516, 5626, 86.34131368937999, 18240.726365868628, 266, 30280, 19001.0, 30034.0, 30036.0, 30044.0, 71.05547255814967, 106.18047784014699, 7.637310205909294], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 4, 0, 0.0, 2856.5, 2830, 2874, 2861.0, 2874.0, 2874.0, 2874.0, 1.3436345314074571, 0.22175218340611355, 0.5222329526368827], "isController": false}, {"data": ["POST /auth/login", 1600, 1270, 79.375, 26245.356874999998, 266, 30249, 30032.0, 30038.0, 30041.0, 30064.9, 31.09211037699184, 80.06560010202098, 1.5280375534395647], "isController": false}, {"data": ["GET /auth/me", 1600, 1572, 98.25, 12655.963749999999, 2795, 30041, 9690.5, 30031.0, 30031.0, 30033.99, 19.735056861632582, 14.022851615499421, 2.6505732802748105], "isController": false}, {"data": ["GET /dashboard/summary", 1596, 1329, 83.27067669172932, 5906.645363408522, 2600, 30043, 4306.0, 7980.199999999999, 26594.19999999999, 30032.0, 29.854096520763186, 11.053715686962214, 5.937649790731387], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 116, 30, 25.862068965517242, 5820.431034482759, 2632, 17870, 2899.5, 14152.4, 14944.25, 17832.6, 5.249581391139069, 0.9406324953613612, 1.7516871634158482], "isController": false}, {"data": ["GET /health", 1600, 1425, 89.0625, 29063.03624999998, 3046, 30280, 30031.0, 30034.0, 30035.0, 30039.0, 19.883186280601468, 48.06296698303716, 0.6107914828507518], "isController": false}]}, function(index, item){
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
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["401/Unauthorized", 2570, 45.680767863490935, 39.44137507673419], "isController": false}, {"data": ["Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 3056, 54.319232136509065, 46.8999386126458], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 6516, 5626, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 3056, "401/Unauthorized", 2570, "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": ["POST /auth/login", 1600, 1270, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 1270, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /auth/me", 1600, 1572, "401/Unauthorized", 1270, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 302, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/summary", 1596, 1329, "401/Unauthorized", 1270, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 59, "", "", "", "", "", ""], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 116, 30, "401/Unauthorized", 30, "", "", "", "", "", "", "", ""], "isController": false}, {"data": ["GET /health", 1600, 1425, "Non HTTP response code: java.net.SocketTimeoutException/Non HTTP response message: Read timed out", 1425, "", "", "", "", "", "", "", ""], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
