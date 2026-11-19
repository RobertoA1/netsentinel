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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.9729842061512884, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.9962640099626401, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9766666666666667, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [1.0, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.9982618771726536, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [1.0, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [1.0, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.7244245524296675, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [1.0, 500, 1500, "GET /health"], "isController": false}, {"data": [0.9948849104859335, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 7639, 0, 0.0, 61.719334991491095, 2, 1369, 27.0, 169.0, 268.0, 428.0, 85.95798309871834, 437.9921218310097, 32.52294107056454], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 829, 0, 0.0, 60.07961399276234, 6, 456, 24.0, 180.0, 261.0, 405.8000000000002, 10.143650735384087, 1.6740986076952256, 3.9425517506668624], "isController": false}, {"data": ["GET /findings", 803, 0, 0.0, 70.4495641344957, 8, 565, 30.0, 189.60000000000002, 319.79999999999995, 486.9200000000001, 10.244306946482109, 231.82746569416977, 4.111728666996236], "isController": false}, {"data": ["POST /auth/login", 150, 0, 0.0, 141.93999999999997, 52, 1369, 72.0, 166.4000000000001, 515.5499999999979, 1346.0500000000004, 7.341784543096275, 15.730346960501198, 1.7494095981596594], "isController": false}, {"data": ["GET /auth/me", 887, 0, 0.0, 49.29425028184899, 5, 463, 17.0, 140.0, 242.79999999999973, 404.72, 10.325840211406154, 17.041669880152735, 3.7814356242942457], "isController": false}, {"data": ["GET /dashboard/summary", 863, 0, 0.0, 75.61297798377758, 10, 504, 34.0, 217.0, 325.39999999999986, 475.72, 10.190706736730235, 5.851694883981815, 3.8314668883214265], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 843, 0, 0.0, 60.37010676156581, 8, 438, 25.0, 176.0, 267.79999999999995, 407.1199999999999, 10.10125217182913, 1.6671011885147684, 3.9063436133245464], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 817, 0, 0.0, 57.195838433292536, 6, 438, 24.0, 170.0, 258.0999999999999, 395.3999999999987, 10.17688091679123, 3.229967087848779, 3.9554673875809665], "isController": false}, {"data": ["GET /alerts/unread-count", 765, 0, 0.0, 58.9464052287582, 6, 436, 25.0, 181.5999999999999, 249.39999999999986, 374.34000000000003, 10.13137680775547, 1.7809060794882663, 3.8289480708997723], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 782, 0, 0.0, 554.1828644501287, 111, 1507, 527.0, 893.0000000000005, 971.6999999999998, 1199.909999999999, 10.124025789078482, 490.0570963255094, 34.67861406763807], "isController": true}, {"data": ["GET /health", 900, 0, 0.0, 28.511111111111116, 2, 291, 9.0, 86.0, 134.94999999999993, 241.97000000000003, 10.294655929721815, 2.231849234763909, 3.759962224331991], "isController": false}, {"data": ["GET /logs", 782, 0, 0.0, 84.97826086956518, 18, 574, 43.0, 227.10000000000014, 326.6499999999992, 525.17, 10.160198526641288, 228.75329788253407, 3.889450998479868], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 7639, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
