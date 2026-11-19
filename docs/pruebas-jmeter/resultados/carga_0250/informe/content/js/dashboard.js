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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.49242424242424243, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.5281767955801105, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.5035211267605634, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.774, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.552917903066271, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.5462487153134635, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.5312163616792249, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.5130830489192264, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.49877300613496933, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.6086538461538461, 500, 1500, "GET /health"], "isController": false}, {"data": [0.49155609167671893, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8483, 0, 0.0, 851.9443593068503, 2, 4163, 868.0, 1111.0, 1241.0, 2908.359999999997, 94.829802694092, 465.69336101252026, 35.721423743083115], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 905, 0, 0.0, 856.4519337016582, 7, 3223, 880.0, 1063.0, 1163.1999999999996, 2363.559999999996, 10.9694310440959, 1.8103846156759837, 4.263509331591962], "isController": false}, {"data": ["GET /findings", 852, 0, 0.0, 986.7629107981218, 12, 3530, 971.0, 1181.7, 1301.7499999999995, 2933.160000000006, 10.790000253286392, 244.17644127871634, 4.3307520547858465], "isController": false}, {"data": ["POST /auth/login", 250, 0, 0.0, 644.8280000000001, 56, 4163, 211.0, 1152.3000000000002, 3236.95, 4066.82, 11.000132001584019, 23.568642198706385, 2.621125203502442], "isController": false}, {"data": ["GET /auth/me", 1011, 0, 0.0, 807.551928783382, 6, 3360, 800.0, 1077.8000000000002, 1325.599999999998, 3141.16, 11.619487639209737, 19.17669346705513, 4.255183461624659], "isController": false}, {"data": ["GET /dashboard/summary", 973, 0, 0.0, 873.3556012332982, 12, 3497, 930.0, 1126.0, 1247.1999999999998, 2699.159999999999, 11.43092105263158, 6.563849198190789, 4.297758403577302], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 929, 0, 0.0, 865.6975242195902, 10, 3374, 886.0, 1079.0, 1200.5, 2886.2000000000135, 11.109516634378513, 1.833504210165985, 4.296258385951066], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 879, 0, 0.0, 887.2536973833904, 8, 3415, 874.0, 1058.0, 1174.0, 3121.2000000000003, 10.854263910498629, 3.444956807531303, 4.218747105838334], "isController": false}, {"data": ["GET /alerts/unread-count", 815, 0, 0.0, 873.6453987730065, 8, 3040, 850.0, 1035.0, 1182.7999999999997, 2532.3600000000024, 10.877108691010035, 1.911991762091608, 4.110782288496957], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 823, 0, 0.0, 7762.682867557717, 1811, 10993, 7777.0, 9312.0, 9884.0, 10506.96, 10.681930275419878, 517.0852300289762, 36.63816705279962], "isController": true}, {"data": ["GET /health", 1040, 0, 0.0, 611.5673076923067, 2, 2267, 644.0, 874.9, 1020.5499999999994, 1939.3599999999997, 11.81751036872905, 2.561999318220556, 4.316161013578774], "isController": false}, {"data": ["GET /logs", 829, 0, 0.0, 1027.3051869722544, 28, 3705, 1002.0, 1241.0, 1338.5, 2687.0000000000146, 10.750178305128705, 242.0364851804124, 4.1153026324320825], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8483, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
