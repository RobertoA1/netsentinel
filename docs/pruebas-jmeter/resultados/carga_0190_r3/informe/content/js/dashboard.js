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
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.8621172919361794, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [0.9668874172185431, 500, 1500, "GET /dashboard/top-talkers"], "isController": false}, {"data": [0.8810623556581986, 500, 1500, "GET /findings"], "isController": false}, {"data": [0.9342105263157895, 500, 1500, "POST /auth/login"], "isController": false}, {"data": [0.9711830131445905, 500, 1500, "GET /auth/me"], "isController": false}, {"data": [0.944041450777202, 500, 1500, "GET /dashboard/summary"], "isController": false}, {"data": [0.967948717948718, 500, 1500, "GET /dashboard/traffic-timeseries"], "isController": false}, {"data": [0.9549600912200684, 500, 1500, "GET /dashboard/findings-by-severity"], "isController": false}, {"data": [0.9695704057279236, 500, 1500, "GET /alerts/unread-count"], "isController": false}, {"data": [0.011229314420803783, 500, 1500, "Sesion tipica: panel + hallazgos + logs"], "isController": true}, {"data": [0.9990138067061144, 500, 1500, "GET /health"], "isController": false}, {"data": [0.8604240282685512, 500, 1500, "GET /logs"], "isController": false}]}, function(index, item){
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
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 8430, 0, 0.0, 293.27081850533716, 3, 949, 287.0, 507.90000000000055, 577.0, 758.380000000001, 94.58094917536184, 474.0866790432515, 35.73307160187367], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["GET /dashboard/top-talkers", 906, 0, 0.0, 295.86203090507735, 10, 869, 294.0, 462.60000000000014, 535.5999999999999, 668.93, 11.102260890876785, 1.8323067290607191, 4.31513655719625], "isController": false}, {"data": ["GET /findings", 866, 0, 0.0, 379.660508083141, 10, 918, 372.0, 596.9000000000002, 694.0, 783.9800000000002, 10.957864102239656, 247.97518050898393, 4.398127095723143], "isController": false}, {"data": ["POST /auth/login", 190, 0, 0.0, 228.03157894736844, 51, 689, 92.0, 527.9, 575.3499999999999, 668.07, 9.072676917199885, 19.43891909798491, 2.161848796676535], "isController": false}, {"data": ["GET /auth/me", 989, 0, 0.0, 251.04550050556134, 6, 802, 252.0, 447.0, 521.5, 634.0, 11.520495765722739, 19.01331820710101, 4.218931554830105], "isController": false}, {"data": ["GET /dashboard/summary", 965, 0, 0.0, 317.5751295336788, 12, 902, 327.0, 510.19999999999993, 585.6999999999999, 739.1000000000005, 11.398131415140025, 6.545020773537437, 4.285430268387607], "isController": false}, {"data": ["GET /dashboard/traffic-timeseries", 936, 0, 0.0, 280.89316239316236, 9, 797, 281.5, 470.0, 536.5999999999999, 656.0, 11.228676311811704, 1.8531702116173612, 4.3423396674584325], "isController": false}, {"data": ["GET /dashboard/findings-by-severity", 877, 0, 0.0, 316.05701254275925, 8, 852, 315.0, 485.0000000000002, 570.1999999999998, 705.0, 10.907010583655651, 3.4616976950078975, 4.239248254194287], "isController": false}, {"data": ["GET /alerts/unread-count", 838, 0, 0.0, 279.28997613365146, 7, 772, 268.0, 442.1, 533.2999999999997, 720.7600000000002, 11.118039616308227, 1.9543429013041804, 4.201837237803988], "isController": false}, {"data": ["Sesion tipica: panel + hallazgos + logs", 846, 0, 0.0, 2735.1099290780217, 859, 4008, 2705.5, 3482.3, 3612.6, 3852.4799999999996, 10.802942077842477, 522.9436071818495, 37.05430681121667], "isController": true}, {"data": ["GET /health", 1014, 0, 0.0, 150.56706114398415, 3, 631, 135.5, 297.0, 363.0, 468.60000000000036, 11.586982356705366, 2.5120215656138587, 4.231964259187311], "isController": false}, {"data": ["GET /logs", 849, 0, 0.0, 412.895170789164, 22, 949, 403.0, 624.0, 738.5, 912.0, 10.9932797265276, 247.50982821786505, 4.208364895311346], "isController": false}]}, function(index, item){
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
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 8430, 0, "", "", "", "", "", "", "", "", "", ""], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
