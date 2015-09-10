#!/usr/bin/env python

""" MultiQC module to parse output from QualiMap """

from __future__ import print_function
import io
import json
import logging
import os

import multiqc
from multiqc import config

# Initialise the logger
log = logging.getLogger('MultiQC : {0:<14}'.format('Qualimap'))

class MultiqcModule(multiqc.BaseMultiqcModule):

    def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__()

        # Static variables
        self.name = "QualiMap"
        self.anchor = "qualimap"
        self.intro = '<p><a href="http://qualimap.bioinfo.cipf.es/" target="_blank">QualiMap</a> \
             is a platform-independent application to facilitate the quality control of alignment \
             sequencing data and its derivatives like feature counts.</p>'

        # Find QualiMap reports
        qualimap_raw_data = {}
        for root, dirnames, filenames in os.walk(config.analysis_dir, followlinks=True):
            if 'genome_results.txt' in filenames and 'raw_data_qualimapReport' in dirnames:
                with io.open(os.path.join(root, 'genome_results.txt'), 'r') as gr:
                    for l in gr:
                        if 'bam file' in l:
                            s_name = self.clean_s_name(os.path.basename(l.split(' = ')[-1]), root)

                s_name = self.clean_s_name(s_name, root)
                if s_name in qualimap_raw_data:
                    log.debug("Duplicate sample name found! Overwriting: {}".format(s_name))
                
                qualimap_raw_data[s_name] = {}
                qualimap_raw_data[s_name]['reports'] = {os.path.splitext(r)[0]: os.path.join(root, 'raw_data_qualimapReport', r) \
                    for r in os.listdir(os.path.join(root, 'raw_data_qualimapReport'))}
                qualimap_raw_data[s_name]['plots'] = {os.path.splitext(r)[0]: os.path.join(root, 'images_qualimapReport', r) \
                    for r in os.listdir(os.path.join(root, 'images_qualimapReport'))}

        if len(qualimap_raw_data) == 0:
            log.debug("Could not find any reports in {}".format(config.analysis_dir))
            raise UserWarning

        log.info("Found {} reports".format(len(qualimap_raw_data)))

        self.sections = list()

        # Section 1 - Coverage Histogram
        histogram_data = self.qualimap_cov_his(qualimap_raw_data)
        if len(histogram_data) > 0:
            self.sections.append({
                'name': 'Coverage Histogram',
                'anchor': 'qualimap-coverage-histogram',
                'content': self.plot_xy_data(histogram_data, {
                    'title': 'Coverage Histogram',
                    'ylab': 'Genome Bin Counts',
                    'xlab': 'Coverage (X)',
                    'ymin': 0,
                    'xmin': 0,
                    'tt_label': '<b>{point.x}-X coverage </b>',
                })
            })


    def qualimap_cov_his(self, qualimap_raw_data):
        parsed_data = {}
        for sn, data in qualimap_raw_data.iteritems():
            cov_report = data['reports'].get('coverage_histogram')
            if cov_report:
                counts={}
                try:
                    with io.open(cov_report, 'r') as fh:
                        next(fh) # skip the header
                        for line in fh:
                            (coverage, count) = line.split(None, 1)
                            coverage = int(round(float(coverage)))
                            count = float(count)
                            counts[coverage] = count

                except IOError as e:
                    log.error("Could not load input file: {}".format(cov_report))
                    raise
                parsed_data[sn] = counts

        return parsed_data


    # def qualimap_cov_his_plot(self, parsed_data):
    #     data = list()
    #     for s in sorted(parsed_data):
    #         pairs = list()
    #         for k, p in iter(sorted(parsed_data[s].items())):
    #             pairs.append([int(k), p])
    #         data.append({
    #             'name': s,
    #             'data': pairs
    #         })
    # 
    #     html = '<div id="qualimap_cov_hist" class="hc-plot"></div> \n\
    #             <script type="text/javascript"> \
    #                 var qualimap-cov_pconfig = {{ \n\
    #                     "title": "Coverage Histogram",\n\
    #                     "ylab": "Genome Bin Counts",\n\
    #                     "xlab": "Coverage (X)",\n\
    #                     "ymin": 0,\n\
    #                     "xmin": 0,\n\
    #                     "tt_label": "<b>{{point.x}}-X coverage </b>",\n\
    #                     "use_legend": false,\n\
    #                 }}; \n\
    #                 $(function () {{ \
    #                     plot_xy_line_graph("#qualimap_cov_hist", {d}, qualimap-cov_pconfig); \
    #                 }}); \
    #             </script>'.format(d=json.dumps(data));
    # 
    #     return html