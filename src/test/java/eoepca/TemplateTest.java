package eoepca;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

public class TemplateTest {

    @Test
    @DisplayName("Template Service unit test")
    public void testTemplate() {

        System.out.println("running unit test");

    }

    @Test
    @DisplayName("Template Service unit test")
    @Disabled
    public void alwaysFail() {

        fail("Failed a test");
    }
}
