# Check if collection exits in database and initialize database only if not
# on command fail restart service
function initialize {
  echo "Initialize coverage types"
  python3 manage.py coveragetype import /rgbnir_definition.json --traceback
  echo "Initializing collection '${COLLECTION}'."
  python3 manage.py producttype create "${COLLECTION}"_Product_COP-DEM_GLO-30-DTED --traceback \
      --coverage-type "int16_grayscale"
  python3 manage.py browsetype create "${COLLECTION}"_Product_COP-DEM_GLO-30-DTED --traceback \
      --red "gray" \
      --red-range -100 4000 \
      --red-nodata 0
  python3 manage.py producttype create "${COLLECTION}"_Product_COP-DEM_GLO-90-DTED --traceback \
      --coverage-type "int16_grayscale"
  python3 manage.py browsetype create "${COLLECTION}"_Product_COP-DEM_GLO-90-DTED --traceback \
      --red "gray" \
      --red-range -100 4000 \
      --red-nodata 0
  python3 manage.py producttype create "${COLLECTION}"_Product_COP-DEM_EEA-10-DGED --traceback \
      --coverage-type "float32_grayscale"
  python3 manage.py browsetype create "${COLLECTION}"_Product_COP-DEM_EEA-10-DGED --traceback \
      --red "gray" \
      --red-range -100 4000 \
      --red-nodata 0
  python3 manage.py producttype create "${COLLECTION}"_Product_COP-DEM_EEA-10-INSP --traceback \
      --coverage-type "float32_grayscale"
  python3 manage.py browsetype create "${COLLECTION}"_Product_COP-DEM_EEA-10-INSP --traceback \
      --red "gray" \
      --red-range -100 4000 \
      --red-nodata 0
  python3 manage.py producttype create "${COLLECTION}"_Product_COP-DEM_GLO-30-DGED --traceback \
      --coverage-type "float32_grayscale"
  python3 manage.py browsetype create "${COLLECTION}"_Product_COP-DEM_GLO-30-DGED --traceback \
      --red "gray" \
      --red-range -100 4000 \
      --red-nodata 0
  python3 manage.py producttype create "${COLLECTION}"_Product_COP-DEM_GLO-90-DGED --traceback \
      --coverage-type "float32_grayscale"
  python3 manage.py browsetype create "${COLLECTION}"_Product_COP-DEM_GLO-90-DGED --traceback \
      --red "gray" \
      --red-range -100 4000 \
      --red-nodata 0
  python3 manage.py collectiontype create "${COLLECTION}"_Collection --traceback 
  python3 manage.py collection create "${COLLECTION}" 
  python3 manage.py collection create "${COLLECTION}_COP-DEM_EEA-10-DGED" 
  python3 manage.py collection create "${COLLECTION}_COP-DEM_EEA-10-INSP" 
  python3 manage.py collection create "${COLLECTION}_COP-DEM_GLO-30-DGED" 
  python3 manage.py collection create "${COLLECTION}_COP-DEM_GLO-30-DTED" 
  python3 manage.py collection create "${COLLECTION}_COP-DEM_GLO-90-DGED" 
  python3 manage.py collection create "${COLLECTION}_COP-DEM_GLO-90-DTED" 
}

id_check=$(python3 manage.py id check "${COLLECTION}")
if [[ $id_check == *"is already in use by a 'Collection'"* ]]; then
  # name is already taken
  echo "Using existing database"
elif [[ $id_check == *"is currently not in use"* ]]; then
  initialize
else
  echo "Restarting service inside init-db by emitting an error"
  set -eo pipefail
  false
fi
