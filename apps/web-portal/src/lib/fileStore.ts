interface PendingFile {
    file: File;
    mode: string;
    source: string;
}

let _pending: PendingFile | null = null;

export const fileStore = {
    set:   (v: PendingFile)        => { _pending = v; },
    get:   ():PendingFile | null   => _pending,
    clear: ()                      => { _pending = null; },
};
