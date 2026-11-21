package io.github.lightzfpwings.basischaracter;

import android.content.*;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;

// Only the OS installer receives a temporary read grant for the specific verified file.
public final class UpdateProvider extends ContentProvider {
    public boolean onCreate() { return true; }
    private File file(Uri u) {
        if (u.getPathSegments().size()!=1 || !u.getLastPathSegment().matches("release-[0-9-]+\\.apk"))
            throw new IllegalArgumentException("Invalid update");
        return new File(new File(getContext().getCacheDir(),"updates"),u.getLastPathSegment());
    }
    public String getType(Uri u) { file(u); return "application/vnd.android.package-archive"; }
    public ParcelFileDescriptor openFile(Uri u,String mode) throws FileNotFoundException {
        if (!"r".equals(mode)) throw new FileNotFoundException();
        return ParcelFileDescriptor.open(file(u),ParcelFileDescriptor.MODE_READ_ONLY);
    }
    public Cursor query(Uri u,String[] projection,String where,String[] args,String order) {
        File f=file(u); String[] cols=projection==null ? new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE}:projection;
        MatrixCursor c=new MatrixCursor(cols); MatrixCursor.RowBuilder row=c.newRow();
        for(String col:cols) row.add(OpenableColumns.DISPLAY_NAME.equals(col)?f.getName():OpenableColumns.SIZE.equals(col)?f.length():null);
        return c;
    }
    public Uri insert(Uri u,ContentValues v) { throw new UnsupportedOperationException(); }
    public int update(Uri u,ContentValues v,String w,String[] a) { throw new UnsupportedOperationException(); }
    public int delete(Uri u,String w,String[] a) { throw new UnsupportedOperationException(); }
}
