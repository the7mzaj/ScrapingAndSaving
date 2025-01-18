public class foo{

    public static int[] specialArr(int[] arr, int med){

        int evenIdx = 0; int oddIdx = 1;

        while(evenIdx < arr.length && oddIdx < arr.length){

            while(evenIdx < arr.length && arr[evenIdx] >= med){
                evenIdx+=2;
            }

            while(oddIdx < arr.length && arr[oddIdx] < med){
                oddIdx+=2;
            }

            if(evenIdx < arr.length){
                swap(arr, evenIdx, oddIdx);
            }
        }
        return arr;
    }

    private static void swap(int[] arr, int i, int j){
        int tmp = arr[i];
        arr[i] = arr[j];
        arr[j] = tmp;
    }
}