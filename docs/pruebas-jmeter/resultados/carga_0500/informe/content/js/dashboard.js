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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.01849906629318394, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.012320328542094456, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.0, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.045, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.025, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.0235, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.021, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.012337662337662338, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.045, 500, 1500, "GET /health"], "isController": false}, {"data": [0.0, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8022, 0, 0.0, 3565.011094490139, 167, 11392, 3437.0, 5063.7, 6855.249999999997, 9869.079999999998, 87.30288288876555, 352.8124961739691, 32.449418171232054], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 974, 0, 0.0, 3514.842915811089, 994, 11038, 3429.0, 3898.0, 6314.5, 9098.25, 12.91982808935109, 2.13227631552767, 5.021573808165756], "isController": false}, {"data": ["GET /findings", 673, 0, 0.0, 3543.9063893016337, 1905, 4236, 3548.0, 3862.2, 3944.0, 4139.82, 11.465857980100859, 259.4710224344504, 4.602019169747512], "isController": false}, {"data": ["POST /auth/login", 500, 0, 0.0, 4081.835999999999, 167, 11165, 3133.0, 7309.9000000000015, 9590.85, 10587.380000000001, 16.43385373870173, 35.210815529991784, 3.9158792111750205], "isController": false}, {"data": ["GET /auth/me", 1000, 0, 0.0, 3545.4499999999935, 1004, 11338, 2794.5, 6679.4, 8285.54999999999, 10913.04, 12.718439193142217, 20.99039280899448, 4.657631540457355], "isController": false}, {"data": ["GET /dashboard/summary", 1000, 0, 0.0, 3735.199000000002, 1061, 11392, 3398.5, 6657.799999999999, 7887.299999999999, 10913.980000000001, 12.434872356035266, 7.140336860692125, 4.675220563548415], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 1000, 0, 0.0, 3647.367999999998, 1013, 11270, 3505.0, 5062.5, 6982.999999999998, 10553.91, 12.537141281045097, 2.0691180434537317, 4.848347604779158], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 770, 0, 0.0, 3336.5805194805207, 1043, 7349, 3414.5, 3809.8, 3884.8999999999996, 4199.309999999995, 11.402846268899848, 3.619067419328565, 4.431965639670058], "isController": false}, {"data": ["GET /alerts/unread-count", 527, 0, 0.0, 3408.6432637571165, 1829, 4159, 3419.0, 3885.0, 4022.5999999999995, 4120.4400000000005, 10.679690349775058, 1.877289319296397, 4.036172036487254], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 546, 0, 0.0, 33728.15018315018, 25229, 38757, 34797.5, 37411.7, 37901.85, 38498.83, 6.895593639888357, 333.76785170211286, 23.585980518527172], "isController": true}, {"data": ["GET /health", 1000, 0, 0.0, 3375.652000000004, 390, 8868, 3044.0, 6258.9, 7209.9, 8516.8, 13.292216078264568, 2.881710907592514, 4.854774231709911], "isController": false}, {"data": ["GET /logs", 578, 0, 0.0, 3598.4498269896185, 3075, 4327, 3572.5, 3849.6000000000004, 3966.45, 4306.47, 10.507562536358348, 236.574076441154, 4.02242628344968], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8022, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
