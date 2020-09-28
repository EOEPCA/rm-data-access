package eoepca;

import io.javalin.Context;
import io.javalin.Javalin;
import io.kubernetes.client.ApiClient;
import io.kubernetes.client.ApiException;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.apis.CoreV1Api;
import io.kubernetes.client.models.*;
import io.kubernetes.client.util.Config;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

//import io.prometheus.client.CollectorRegistry;
//import io.prometheus.client.exporter.common.TextFormat;


public class TemplateService {


    private static final Logger logger = LoggerFactory.getLogger(TemplateService.class);

    // The namespace where the batch job will be executed
    private static final String TARGET_NAMESPACE = "eo-user-compute"; //"eo`-services";
//    private static final CollectorRegistry registry = CollectorRegistry.defaultRegistry;

    public static void main(String[] args) {
        Javalin app = Javalin.create().start(7000);

        String db_user = System.getenv("DB_USERNAME");
        String db_password = System.getenv("DB_PASSWORD");


        if (db_user != null & db_password != null)
            // Travis magically hides all secure env variables longer than 3 chars - seemingly using a simple case sensitive string match
            // and replaces them with [secure] in the console.  Changing them to upper case to subvert this feature.
            logger.debug("Database credentials: username = {}, password = {}", db_user.toUpperCase(), db_password.toUpperCase());
        else
            logger.error("Database credentials missing: username = {}, password = {}", db_user, db_password);

        app.get("/ping", ctx -> ctx.result("Hello World "));

        app.get("/search", ctx -> {

          logger.debug("Searching catalogue...");

          SearchResult out = new SearchResult();
          out.result = "search results";
          ctx.json(out);
        } );

        // should be a POST
        app.get("/process", TemplateService::spawnBatchJob);

        app.get("/metrics", TemplateService::metrics);

        app.get("/volumes", TemplateService::listPersistentVolumes);
    }

    /**
     * apiVersion: batch/v1
     * kind: Job
     * metadata:
     *   name: pi
     * spec:
     *   template:
     *     spec:
     *       containers:
     *       - name: pi
     *         image: perl
     *         command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
     *       restartPolicy: Never
     *   backoffLimit: 4
     * @param ctx
     */


    public static void spawnBatchJob(Context ctx) {
        logger.debug(">>>>> SPAWNING JOB");

        try {

            V1Job job = defineJob();
            logger.debug(">>>>> JOB DEFINED");
            V1Job jobResult = launchBatch(job, TARGET_NAMESPACE);
            logger.debug(">>>>> JOB Resource {}", jobResult);

            JobSummary js = new JobSummary();

            DateTime startTime = jobResult.getStatus().getStartTime();
            if (startTime != null) {
                js.startTS = startTime.toDateTimeISO().toString();
//                        LocalDateTime.of(startTime.year().get(),
//                        startTime.monthOfYear().get(),
//                        startTime.dayOfMonth().get(),
//                        startTime.hourOfDay().get(),
//                        startTime.minuteOfHour().get(),
//                        startTime.secondOfMinute().get());
            }
            js.name = jobResult.getMetadata().getName();
            js.id = jobResult.getMetadata().getUid();
            js.createdTS = jobResult.getMetadata().getCreationTimestamp().toDateTimeISO().toString();
            //js.id = jobResult.getSpec().getSelector().toString();

            // TODO this is the PVC name in the podspec NOT the actual volume name.  Can get this via the PVC.
            js.volume = jobResult.getSpec().getTemplate().getSpec().getVolumes().get(0).getPersistentVolumeClaim().getClaimName();

            ctx.json(js);


        } catch (IOException | ApiException | NullPointerException e) {
            logger.error(">>>>>>> Batch Execution Exception cause {} {} ", e.getCause(), e.getMessage());
            ctx.status(500);
        }
    }

    /**
     * To launch a batch job need:
     *
     * - The Job definition
     * - The target namespace where the job (containers) will execute
     * - The K8S API credentials to launch the job - in this case a service account
     */

    public static V1Job launchBatch(V1Job job, String namespace) throws IOException, ApiException {

        // attempts to work out where the code is running.  If inside a cluster it will locate the
        // container's/pod's service account CA cert and service account token from their mount paths
        // and create a token from them
        //Config.fromCluster()  assumes running inside a cluster - use defaultClient instead
        ApiClient apiClient = Config.defaultClient();


        //Configuration.setDefaultApiClient(apiClient)
        BatchV1Api apiInstance = new BatchV1Api(apiClient);

        String pretty = "true"; // String | If 'true', then the output is pretty printed.
        try {
            V1Job result = apiInstance.createNamespacedJob(namespace, job, pretty);
            return result;
        } catch (ApiException e) {  // TODO improve this
            logger.error(e.getResponseBody());
            logger.error(">>>>> Code {} Message {}", e.getCode(), e.getMessage());
            throw e;
        }
    }


    public static V1Job defineJob() {
        V1Job job = new V1Job();
        V1ObjectMeta metadata = new V1ObjectMeta();
        V1JobSpec jobSpec = new V1JobSpec();
        V1PodTemplateSpec template = new V1PodTemplateSpec();
        V1PodSpec podSpec = new V1PodSpec();
        V1Container container = new V1Container();
        V1VolumeMount mnt = new V1VolumeMount();
        V1Volume vol = new V1Volume();
        List<V1Container> containers = List.of(container);
        List<V1VolumeMount> mounts = List.of(mnt);
        List<V1Volume> volumes = List.of(vol);
        V1PersistentVolumeClaimVolumeSource pvc = new V1PersistentVolumeClaimVolumeSource();

        metadata.name("pi");

        metadata.namespace(TARGET_NAMESPACE);

        job.apiVersion("batch/v1");
        job.kind("Job");
        job.metadata(metadata);

        job.spec(jobSpec);
        jobSpec.template(template);
        jobSpec.setBackoffLimit(4);

        template.spec(podSpec);
        podSpec.containers(containers);
        podSpec.setRestartPolicy("Never");
        podSpec.automountServiceAccountToken(false);  // prevents access to the K8S API from inside the batch pod

        container.name("pi");
        container.image("perl");
        container.command(List.of("perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"));
        container.volumeMounts(mounts);

        mnt.name("eo-data-volume");  // must match volume name
        mnt.mountPath("/var/eo-data");

        podSpec.volumes(volumes);

        vol.name("eo-data-volume");
        vol.persistentVolumeClaim(pvc);

        pvc.claimName("pvc-sample-eo-data");  // must match the claim name defined in YAML

        return job;
    }

    public static void listPersistentVolumes(Context ctx) {

        String label = ctx.queryParam("label", "vol-type=eo-end-user-data");  // default value

        logger.info("URL is {} Label value  is {}", ctx.url(), label);

        ApiClient apiClient = null;
        try {
            apiClient = Config.defaultClient();
        } catch (IOException e) {
            logger.error(">>>>> API Client IOException {}", e.getMessage());
        }

        CoreV1Api api = new CoreV1Api(apiClient);

        try {
            V1PersistentVolumeList vols = api.listPersistentVolume("true", null, null, true, label, 10, null, null, false);

            if (vols != null) {
                logger.info(vols.toString());

                List<VolumeSummary> volSummaries = new ArrayList<>();

                for (V1PersistentVolume vol : vols.getItems()) {
                    VolumeSummary v = new VolumeSummary();
                    v.name = vol.getMetadata().getName();
                    v.capacity = vol.getSpec().getVolumeMode();
                    v.status = vol.getStatus().getPhase();

                    volSummaries.add(v);
                }

                ctx.json(volSummaries);
                ctx.status(200);
            }

            else {
                ctx.result("Volumes not found");
                ctx.status(404);
            }
        }
        catch (ApiException e) {
            logger.error(e.getResponseBody());
            logger.error(">>>>> Code {} Message {}", e.getCode(), e.getMessage());
            ctx.result("Container API error");
            ctx.status(502);
        }
        catch(Exception e) {
            logger.error(">>>>> type {} Message {}", e.getClass().getName(), e.getMessage());
            ctx.result("Volume error "+e.getClass().getName());
            ctx.status(500);
        }
    }


    // Code adapted from
    // https://github.com/prometheus/client_java/blob/master/simpleclient_servlet/src/main/java/io/prometheus/client/exporter/MetricsServlet.java
    // https://cloud.google.com/solutions/best-practices-for-operating-containers
    public static void metrics(Context ctx) throws IOException {

//        HttpServletResponse resp = ctx.res;
//        resp.setStatus(HttpServletResponse.SC_OK);
//        resp.setContentType(TextFormat.CONTENT_TYPE_004);
//
//        Writer writer = resp.getWriter();
//        try {
//            TextFormat.write004(writer, registry.filteredMetricFamilySamples(Set.of());
//            writer.flush();
//        } finally {
//            writer.close();
//        }
    }
}


class SearchResult {

    String result;

    public String getResult() {
        return result;
    }

    public void setResult(String res) {
        result = res;
    }   
}

class JobSummary {
    String name;
    String id;
    String volume;
    String startTS;
    String createdTS;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getVolume() {
        return volume;
    }

    public void setVolume(String volume) {
        this.volume = volume;
    }

    public String getStartTS() {
        return startTS;
    }

    public void setStartTS(String startTS) {
        this.startTS = startTS;
    }

    public String getCreatedTS() {
        return createdTS;
    }

    public void setCreatedTS(String createdTS) {
        this.createdTS = createdTS;
    }
}

class VolumeSummary {
    String name;
    String capacity;
    String status;

    public String getCapacity() {
        return capacity;
    }

    public void setCapacity(String capacity) {
        this.capacity = capacity;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
