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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9462977563154955, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9844674556213018, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.9726775956284153, 500, 1500, "GET /findings"], "isController": false}, {"data": [1.0, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9869515576578046, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.9766187050359713, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.9826992456543129, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9856435643564356, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.9872796807449284, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.614809895400963, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9965006510416666, 500, 1500, "GET /health"], "isController": false}, {"data": [0.9706956666113232, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 54859, 0, 0.0, 99.56798337556366, 2, 1113, 50.0, 341.0, 471.0, 718.9900000000016, 91.6496400606108, 488.7330993880446, 34.92489898892867], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 6084, 0, 0.0, 99.80802103879043, 6, 900, 33.0, 295.5, 429.0, 675.5999999999985, 10.288166748117472, 1.6979493949529811, 3.9987210603034704], "isController": false}, {"data": ["GET /findings", 6039, 0, 0.0, 119.4417949991719, 8, 1098, 41.0, 343.0, 519.0, 831.2000000000025, 10.270146169740569, 232.41220428847478, 4.122099683362669], "isController": false}, {"data": ["POST /auth/login", 150, 0, 0.0, 83.73333333333333, 52, 408, 66.0, 119.0, 173.45, 403.9200000000001, 4.9769401771790704, 10.6634831530575, 1.1859115265934503], "isController": false}, {"data": ["GET /auth/me", 6131, 0, 0.0, 85.77165225901157, 4, 889, 27.0, 257.0, 393.39999999999964, 627.0, 10.290210453349983, 16.982866861485814, 3.7683876171935973], "isController": false}, {"data": ["GET /dashboard/summary", 6116, 0, 0.0, 118.82472204054926, 9, 1067, 46.0, 336.0, 484.0, 761.1499999999996, 10.291375840507232, 5.9095009709162625, 3.8693161119094577], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 6098, 0, 0.0, 100.75664152181062, 6, 1021, 35.0, 289.0, 430.0, 701.0, 10.288857393534453, 1.69806337842512, 3.9788940701559024], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 6060, 0, 0.0, 97.58300330032998, 6, 966, 32.0, 295.0, 417.9499999999998, 682.7800000000007, 10.277649165831395, 3.261949198139847, 3.9946331718758743], "isController": false}, {"data": ["GET /alerts/unread-count", 6014, 0, 0.0, 92.95044895244422, 5, 929, 31.0, 270.0, 388.0, 652.5500000000011, 10.283031288525034, 1.807564093686041, 3.886262801424988], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 6023, 0, 0.0, 901.5198406109921, 105, 4242, 616.0, 1942.6000000000004, 2600.800000000001, 3365.76, 10.26279782646108, 496.81092839992453, 35.232482767364374], "isController": true}, {"data": ["GET /health", 6144, 0, 0.0, 49.837076822916664, 2, 720, 13.0, 148.0, 217.0, 440.0, 10.290974627655654, 2.2310511399800346, 3.7586176862726703], "isController": false}, {"data": ["GET /logs", 6023, 0, 0.0, 132.41424539266208, 17, 1113, 51.0, 366.0, 550.8000000000002, 882.0, 10.263532338732352, 231.07982233347107, 3.9290084734209785], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 54859, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
