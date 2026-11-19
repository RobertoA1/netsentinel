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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.4859478521051507, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.5242290748898678, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.47560975609756095, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.81, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.5498519249753209, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.5360453141091658, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.5331550802139038, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.5130681818181818, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.48902439024390243, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.0035971223021582736, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.611904761904762, 500, 1500, "GET /health"], "isController": false}, {"data": [0.4611244019138756, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8524, 0, 0.0, 836.1371421867674, 3, 1725, 851.0, 1156.0, 1373.75, 1587.75, 95.52840972767007, 470.99487892945194, 35.98732953112742], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 908, 0, 0.0, 845.4889867841409, 10, 1642, 856.5, 1084.0, 1268.1999999999998, 1495.37, 11.044213343063918, 1.8227266161892597, 4.292575107948671], "isController": false}, {"data": ["GET /findings", 861, 0, 0.0, 1000.677119628339, 20, 1725, 968.0, 1312.4, 1544.5, 1680.76, 10.821613061347612, 244.8918354205158, 4.343440398646355], "isController": false}, {"data": ["POST /auth/login", 250, 0, 0.0, 435.17599999999993, 55, 1484, 137.0, 1126.6000000000001, 1191.9, 1465.8000000000002, 11.781338360037699, 25.24243785344015, 2.8072720311027335], "isController": false}, {"data": ["GET /auth/me", 1013, 0, 0.0, 760.227048371175, 7, 1599, 769.0, 1088.2, 1303.3999999999996, 1540.0, 11.717620386114678, 19.338650832552545, 4.2911207468681685], "isController": false}, {"data": ["GET /dashboard/summary", 971, 0, 0.0, 849.6982492275997, 13, 1647, 877.0, 1137.4, 1366.5999999999997, 1595.3999999999999, 11.412787964268924, 6.553436838857546, 4.2909407873472025], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 935, 0, 0.0, 827.1411764705892, 11, 1608, 844.0, 1083.4, 1323.0, 1531.5199999999998, 11.205253885886174, 1.849304596401136, 4.3332817761825435], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 880, 0, 0.0, 875.4625000000007, 11, 1640, 866.0, 1119.8, 1356.8999999999999, 1545.9499999999998, 10.868088574921886, 3.449344518407825, 4.224120364080967], "isController": false}, {"data": ["GET /alerts/unread-count", 820, 0, 0.0, 875.9829268292676, 501, 1605, 835.5, 1216.8999999999996, 1383.7499999999995, 1538.79, 10.842401724206324, 1.9058909280831426, 4.097665495378757], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 834, 0, 0.0, 7718.335731414867, 1309, 9549, 8007.0, 8924.0, 9056.0, 9286.65, 10.71277183337401, 518.5648857673633, 36.71534305114899], "isController": true}, {"data": ["GET /health", 1050, 0, 0.0, 631.8628571428566, 3, 1436, 643.0, 969.9, 1162.4499999999998, 1393.47, 11.927074459021979, 2.585752470608281, 4.356177585619356], "isController": false}, {"data": ["GET /logs", 836, 0, 0.0, 1038.8026315789473, 462, 1725, 1000.5, 1455.2000000000003, 1554.6, 1670.26, 10.730329867796176, 241.58960459183675, 4.107704402515724], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8524, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
