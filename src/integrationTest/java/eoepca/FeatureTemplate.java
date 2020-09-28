package eoepca;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.ResponseBody;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.List;

public class FeatureTemplate {


    private static String endpointUrl = "";

    public static final String SEARCH_SERVICE_HOST = "SEARCH_SERVICE_HOST";
    public static final String SEARCH_SERVICE_PORT = "SEARCH_SERVICE_PORT";

    public static final String DEFAULT_HOST = "localhost";  // defaults when running as a JAR file outside of Docker
    public static final int DEFAULT_PORT = 7000;

    @BeforeAll
    public static void endpointURL() {
        String host = System.getenv(SEARCH_SERVICE_HOST);
        String port = System.getenv(SEARCH_SERVICE_PORT);

        if (host == null) {

            host = DEFAULT_HOST;
        }

        if (port == null) {
            port = String.valueOf(DEFAULT_PORT);
        }

        endpointUrl = "http://"+host+":"+port;
    }

    @Test
    @DisplayName("Search the catalogue for dataset")
    public void searchForDataset() throws IOException {
        OkHttpClient client = new OkHttpClient();


        Request request = new Request.Builder()
            .url(endpointUrl+"/search")
            .build();

        Response response = client.newCall(request).execute();
        assertEquals(200, response.code());

        ObjectMapper mapper = new ObjectMapper();

        SearchResult out = mapper.readValue(response.body().string(), SearchResult.class);

        assertEquals("search results", out.result);
    }

    @Test
    @DisplayName("Spawns a batch job")
    public void spawnJob() throws IOException {
        OkHttpClient client = new OkHttpClient();


        Request request = new Request.Builder()
                .url(endpointUrl+"/process")
                .build();

        Response response = client.newCall(request).execute();
        assertEquals(200, response.code());

        if (response.code() <= 201) {
            ObjectMapper mapper = new ObjectMapper();

            String body = response.body().string();
            JobSummary out = mapper.readValue(body , JobSummary.class);

            System.out.println("Integration test response - Job Summary : " + body);
        }

        // TODO assert on job summary
    }

    @Test
    @DisplayName("Selects all volumes of a type")
    public void selectVolumes() throws IOException {
        OkHttpClient client = new OkHttpClient();


        Request request = new Request.Builder()
                .url(endpointUrl+"/volumes")
                .build();

        Response response = client.newCall(request).execute();

        System.out.println("Status code: "+response.code());
        assertEquals(200, response.code());

        ResponseBody rbody = response.body();

        if (response.code() <= 201) {
            ObjectMapper mapper = new ObjectMapper();

            String body = rbody.string();
            List<VolumeSummary> out = mapper.readValue(body , new TypeReference<List<VolumeSummary>>(){});

            System.out.println("Integration test response - Volume Summary : " + body);
        }
        else if (rbody != null) {
            System.out.println(rbody.string());
        }

        // TODO assert on vol summary
    }

    @Test
    @DisplayName("Selects a volume")
    public void selectSpecificVolume() throws IOException {
        OkHttpClient client = new OkHttpClient();


        Request request = new Request.Builder()
                .url(endpointUrl+"/volumes?label=vol-type%3Deo-end-user-data,vol-id%3Dvol_0001")
                .build();

        Response response = client.newCall(request).execute();

        System.out.println("Status code: "+response.code());
        assertEquals(200, response.code());

        ResponseBody rbody = response.body();

        if (response.code() <= 201) {
            ObjectMapper mapper = new ObjectMapper();

            String body = rbody.string();
            List<VolumeSummary> out = mapper.readValue(body , new TypeReference<List<VolumeSummary>>(){});

            System.out.println("Integration test response - Volume Summary : " + body);
        }
        else if (rbody != null) {
            System.out.println(rbody.string());
        }

        // TODO assert on vol summary
    }


    @Test
    @DisplayName("No Op Test to test Gradle logging")
    @Disabled
    public void noopTest() {
        System.out.println("No-Op test to stdout");
    }

    @Test
    @DisplayName("Always Fail Test to test Gradle logging")
    @Disabled
    public void failingTest() {
        System.out.println("Failing test to stdout");
        fail("I've failed!");
    }
}
