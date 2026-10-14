import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
import brut.androlib.src.SmaliBuilder;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile;
import com.android.tools.smali.dexlib2.writer.builder.DexBuilder;
import com.android.tools.smali.dexlib2.writer.io.FileDataStore;
import com.android.tools.smali.baksmali.Baksmali;
import com.android.tools.smali.baksmali.BaksmaliOptions;

/** Thin API adapter for the pinned Apktool 2.12.1 bundled smali implementation. */
public class SmaliTool {
    public static void main(String[] args) throws Exception {
        Opcodes opcodes = new Opcodes(28, -1);
        if (args[0].equals("disassemble")) {
            BaksmaliOptions options = new BaksmaliOptions();
            options.localsDirective = true;
            options.sequentialLabels = true;
            options.debugInfo = true;
            Baksmali.disassembleDexFile(new DexBackedDexFile(opcodes,
                    Files.readAllBytes(Path.of(args[1])), 0), new File(args[2]), 4, options);
        } else if (args[0].equals("assemble")) {
            Path root = Path.of(args[1]);
            SmaliBuilder builder = new SmaliBuilder(root.toFile(), 28);
            DexBuilder dex = new DexBuilder(opcodes);
            try (Stream<Path> files = Files.walk(root)) {
                files.filter(p -> p.toString().endsWith(".smali")).sorted()
                    .forEach(p -> builder.buildFile(root.relativize(p).toString(), dex));
            }
            FileDataStore out = new FileDataStore(new File(args[2]));
            dex.writeTo(out);
            out.raf.close();
        } else throw new IllegalArgumentException("assemble|disassemble");
    }
}
