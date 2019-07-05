/*
 * xnat-workshop: org.nrg.xnat.workshop.plugin.WorkshopXnatPlugin
 * XNAT http://www.xnat.org
 * Copyright (c) 2017, Washington University School of Medicine
 * All Rights Reserved
 *
 * Released under the Simplified BSD.
 */

package org.nrg.xnat.workshop.plugin;

import org.nrg.framework.annotations.XnatDataModel;
import org.nrg.framework.annotations.XnatPlugin;
import org.nrg.xdat.bean.WorkshopBiosamplecollectionBean;
import org.nrg.xdat.bean.RadRadiologyreaddataBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;

@XnatPlugin(value = "workshopPlugin", name = "XNAT 1.7 Workshop 2016 Plugin", entityPackages = "org.nrg.xnat.workshop.entities",
            dataModels = {@XnatDataModel(value = WorkshopBiosamplecollectionBean.SCHEMA_ELEMENT_NAME,
                                         singular = "Biosample Collection",
                                         plural = "Biosample Collections"),
                          @XnatDataModel(value = RadRadiologyreaddataBean.SCHEMA_ELEMENT_NAME,
                                         singular = "Radiology Read",
                                         plural = "Radiology Reads")})
@ComponentScan({"org.nrg.xnat.workshop.subjectmapping.preferences",
        "org.nrg.xnat.workshop.subjectmapping.repositories",
        "org.nrg.xnat.workshop.subjectmapping.rest",
        "org.nrg.xnat.workshop.subjectmapping.services.impl"})
public class WorkshopXnatPlugin {
    @Bean
    public String workshopPluginMessage() {
        return "Hello there from the workshop plugin!";
    }
}
