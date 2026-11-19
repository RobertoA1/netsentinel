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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.8601258270962143, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.958980044345898, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.8799303944315545, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9842105263157894, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9730142566191446, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.9295478443743428, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.9606256742179072, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9517593643586834, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.978391356542617, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.02431791221826809, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [0.842603550295858, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8376, 0, 0.0, 310.6199856733515, 2, 821, 322.0, 511.0, 567.0, 671.2299999999996, 94.3391976212466, 473.6223743924999, 35.64229844091411], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 902, 0, 0.0, 317.64523281596405, 8, 644, 331.0, 484.70000000000005, 549.0, 624.8500000000001, 11.089663990557803, 1.8302277484416685, 4.310240496330083], "isController": false}, {"data": ["GET /findings", 862, 0, 0.0, 404.25522041763327, 16, 821, 419.0, 574.0, 648.2499999999995, 722.8100000000001, 10.891952338231764, 246.48360501352016, 4.3716722763801314], "isController": false}, {"data": ["POST /auth/login", 190, 0, 0.0, 185.2631578947368, 55, 542, 84.0, 450.30000000000007, 490.0499999999999, 537.45, 9.228676899164562, 19.77316124684282, 2.1990206673790555], "isController": false}, {"data": ["GET /auth/me", 982, 0, 0.0, 271.41446028513246, 7, 627, 291.0, 457.70000000000005, 509.0, 574.6799999999998, 11.443487583466375, 18.88622462505681, 4.19073031621083], "isController": false}, {"data": ["GET /dashboard/summary", 951, 0, 0.0, 339.0283911671924, 13, 752, 360.0, 528.0, 591.8, 680.0, 11.231045396570456, 6.449076848811941, 4.22260984148401], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 927, 0, 0.0, 308.6375404530745, 9, 677, 325.0, 481.20000000000005, 546.1999999999998, 629.8800000000001, 11.165446136057042, 1.842734762689102, 4.31788737292831], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 881, 0, 0.0, 319.71509648127073, 8, 697, 331.0, 495.80000000000007, 564.0, 627.3599999999999, 10.972997210043841, 3.482640716078368, 4.264895399997509], "isController": false}, {"data": ["GET /alerts/unread-count", 833, 0, 0.0, 299.82352941176487, 8, 595, 306.0, 433.20000000000005, 492.29999999999995, 563.66, 11.003381591461482, 1.9341881703740886, 4.15850456630429], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 843, 0, 0.0, 2887.537366548041, 155, 4349, 2874.0, 3728.6, 3963.3999999999996, 4165.279999999999, 10.993453483216399, 532.1611416507459, 37.69776785132104], "isController": true}, {"data": ["GET /health", 1003, 0, 0.0, 158.5653040877368, 2, 456, 162.0, 280.0, 326.79999999999995, 410.8000000000002, 11.520128639522197, 2.4975278886464136, 4.207546983575489], "isController": false}, {"data": ["GET /logs", 845, 0, 0.0, 433.1999999999998, 23, 803, 441.0, 617.4, 674.6999999999999, 745.0, 10.928608380755303, 246.0537756038218, 4.1836078957578895], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8376, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
